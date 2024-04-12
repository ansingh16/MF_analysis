import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import altair as alt
import multiprocessing.pool as Pool
import re


# Donut chart
def make_donut(type):

    if type=="portfolio":
        input_df = st.session_state["portfolio"]
        # Calculate category counts
        category_counts = input_df['Scheme Category Name'].value_counts().reset_index()
        category_counts.columns = ['Scheme Category Name', 'count']
        # Create a donut chart
        donut = alt.Chart(category_counts).mark_arc(innerRadius=20).encode(
            theta="count",
            color="Scheme Category Name:N",
        )
        return donut
        
    elif type=="scheme":
        input_df = st.session_state["consol_holdings"]

        input_df = input_df.loc[input_df['Scheme Name'] == st.session_state.scheme]
        # Calculate category counts
        category_counts = input_df['sector_name'].value_counts().reset_index()
        category_counts.columns = ['sector_name', 'count']
        # Create a donut chart
        donut = alt.Chart(category_counts).mark_arc(innerRadius=20).encode(
            theta="count",
            color="sector_name:N",
        )
        return donut
        
    
    elif type=="value":
        mf_portfolio = st.session_state["portfolio"]
        # Calculate current value in schemes
        scheme_value = mf_portfolio['Units'] * mf_portfolio['NAV']
        # get total value
        total_value = scheme_value.sum()
        mf_portfolio['Fraction Value'] = (scheme_value / total_value)*100

        # Group by Scheme Category Name and calculate the sum of the Fraction Value
        category_value = mf_portfolio.groupby('Scheme Category Name')['Fraction Value'].sum().reset_index()

        # Create the donut chart
        donut = alt.Chart(category_value).mark_arc(innerRadius=20).encode(
            color='Scheme Category Name:N',
            theta='Fraction Value',
            tooltip=['Scheme Category Name', alt.Tooltip('Fraction Value:Q', title='Percentage Allocated', format='.2f')]
        )
        
        
        return donut
    
    elif type=="sector_value":
        consol_df = st.session_state["consol_holdings"]
        # Calculate current value in schemes
        all_scheme_value = consol_df['Units'] * consol_df['NAV']
        # get total value
        total_value = all_scheme_value.sum()
        consol_df['Fraction Value'] = (all_scheme_value / total_value)*100

        # Group by Scheme Category Name and calculate the sum of the Fraction Value
        category_value = consol_df.groupby('sector_name')['Fraction Value'].sum().reset_index()

        # Create the donut chart
        donut = alt.Chart(category_value).mark_arc(innerRadius=20).encode(
            color='sector_name:N',
            theta='Fraction Value',
            tooltip=['sector_name', alt.Tooltip('Fraction Value:Q', title='Percentage Allocated', format='.2f')]
        ).mark_arc(innerRadius=20,outerRadius=80)
        
        
        return donut
    
def get_top_companies():
    """
    Function to get top companies
    """
    consol_df = st.session_state["consol_holdings"]

    # get value invested in a company
    consol_df['company_value']  = consol_df['Units'] * consol_df['NAV']*consol_df['corpus_per']
    
    # percent invested in a company with respect to total value of all companies
    consol_df['percent_value'] = (consol_df['company_value']/consol_df['company_value'].sum())*100

    # group by company_name and calculate the sum of the value and sort in descending order
    top_companies = consol_df.groupby('company_name')['percent_value'].sum().reset_index().sort_values(by='percent_value', ascending=False)

    return top_companies.head(10)

# get holdings
def get_scheme_holdings():
    """
    filter the holdings based on the selected scheme
    """
    scheme_df = st.session_state["consol_holdings"]

    hold_df = scheme_df.loc[scheme_df['Scheme Name'] == st.session_state.scheme]

    return hold_df



@st.cache_data
def get_consolidated_holdings(schemei):
    """
    Function to get consolidated holdings from all MF portfolio
    """
    
    mf_portfolio = st.session_state["portfolio"]
    
    Units = mf_portfolio.loc[mf_portfolio['Scheme Name'] == schemei,'Units'].values[0]
    # get url
    url = requests.get(mf_portfolio.loc[mf_portfolio['Scheme Name'] == schemei,'scheme_url'].values[0])
    # scrape url
    soup = BeautifulSoup(url.text, 'html.parser')

    # Find the script tag with the specific ID
    script_tag = soup.find('script', id='__NEXT_DATA__')

    # Extract the JSON data from the script tag content
    json_data = json.loads(script_tag.contents[0])

    # get holdings
    holdings = json_data['props']['pageProps']['mf']['holdings']

    # get NAV

    td_tag = soup.find_all('td',class_="fd12Cell contentPrimary bodyLargeHeavy")[0]

    # Extract the text content from the <td> tag
    value = td_tag.get_text(strip=True)

    # get NAV
    NAV= re.search(r'₹([\d.]+)', value).group(1)

    # get category
    category = json_data['props']['pageProps']['mf']['category']
    # get sub-category
    subcategory = json_data['props']['pageProps']['mf']['sub_category']

    # get pandas
    hold_df = pd.DataFrame(holdings)
    hold_df['Scheme Name'] = schemei
    hold_df['NAV'] = float(NAV)
    hold_df['Units'] = Units
    hold_df['Scheme Category'] = category
    hold_df['Scheme Sub-Category'] = subcategory

    # get other sectors not in the list
    # Calculate the sum of contrib_per
    total_contrib_per = hold_df['corpus_per'].sum()

    # Check if the sum is less than 1
    if total_contrib_per < 1:
        # Calculate the contribution percentage for 'Other'
        other_contrib_per = 1 - total_contrib_per
        
        # Append a new row for 'Other'
        hold_df = hold_df.append({'company_name': 'Other', 'contrib_per': other_contrib_per}, ignore_index=True)

        
    # hold_df = hold_df[['company_name','sector_name','corpus_per']]

    if not hold_df.empty:
        hold_df = hold_df[['Scheme Name','company_name','sector_name','corpus_per','NAV','Units']]
    
    return hold_df



# Function to load data
@st.cache_data
def analyze_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        # Read the uploaded file into a pandas DataFrame
        df = pd.read_csv(uploaded_file)
        return df



def add_entry(url, units):
    # Check if dataframe exists in session state
    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = pd.DataFrame(columns=["Scheme Name", "Scheme Category","NAV","Units"])

    # read url
    url_text =  requests.get(url)
    soup = BeautifulSoup(url_text.text, 'html.parser')
    # Get the scheme name
    scheme_name = soup.find_all('title')[0].get_text().split('-')[0].strip()
    
    # Find the script tag with the specific ID
    script_tag = soup.find('script', id='__NEXT_DATA__')

    # Extract the JSON data from the script tag content
    json_data = json.loads(script_tag.contents[0])

    # get NAV

    td_tag = soup.find_all('td',class_="fd12Cell contentPrimary bodyLargeHeavy")[0]

    # Extract the text content from the <td> tag
    value = td_tag.get_text(strip=True)
    # get NAV
    NAV= re.search(r'₹([\d.]+)', value).group(1)

    # get category
    category = json_data['props']['pageProps']['mf']['category']
    # get subcategory
    subcategory = json_data['props']['pageProps']['mf']['sub_category']

    # Append the new entry to the dataframe
    st.session_state["portfolio"] = st.session_state["portfolio"].append(
        {"Scheme Name": scheme_name, "Units": units, "NAV": float(NAV), "Scheme Category Name": category+" - "+subcategory,"scheme_url": url}, ignore_index=True
    )


    st.success("Entry added successfully.")

def display_entries():
    # Display the dataframe with checkboxes for selection
    st.subheader("Schemes Added to Portfolio")
    if "portfolio" in st.session_state:
        for index, row in st.session_state["portfolio"].iterrows():
            st.checkbox(f"{row['Scheme Name']} - {row['Units']}", key=index)


def main():
    st.title("Mutual Fund Portfolio Analysis")

    # Initialize session state if not already initialized
    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = pd.DataFrame(columns=['Scheme Name', 'Units'])


    with st.sidebar:
        # Set title
        st.header("Add Mutual Fund Entry")
        # Define inputs for each column
        scheme_url = st.text_input("Groww url")
        scheme_units = st.number_input("Units", min_value=0, step=1)
        st.session_state.input_data = pd.DataFrame(columns=["Company", "Contribution"])

        # Add a button to add the entry
        if st.button("Add Entry"):
            
            # Validate inputs
            if scheme_url.strip() == "":
                st.error("Please enter a valid scheme name")
                return
            else:
                input_url = scheme_url
            if scheme_units <= 0:
                st.error("Contribution must be a positive number.")
                return
            else:
                input_units = scheme_units

            # if both inputs are valid, add the entry
            if input_url and input_units:
                add_entry(input_url, input_units)
            
        
        
        st.header('OR')

        st.header("Upload CSV File")

        uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

    
        # Button to Analyze Uploaded File
        if uploaded_file is not None:
            if st.sidebar.button("Analyze"):
                # Perform analysis on the uploaded file
                df = analyze_uploaded_file(uploaded_file)
                # Update session state with analyzed DataFrame
                st.session_state["portfolio"] = df

        display_entries()

    if st.session_state["portfolio"].shape[0]>0:


        # get consolidated holdings
        all_schemes = st.session_state["portfolio"]['Scheme Name'].unique()
                    
        with st.spinner("Calculating Consolidated Holdings..."):
                            
            with Pool.Pool(4) as p:

                # use map to run in parallel on all schemes
                consol_holdings_list = p.map(get_consolidated_holdings, all_schemes)

                # concat the list of dataframes into a single dataframe
                consol_holdings = pd.concat(consol_holdings_list, ignore_index=True)



                # consolidated holdings
                            
                st.session_state["consol_holdings"] = consol_holdings

            
    # # Display the contents of the uploaded file
    # if st.session_state["portfolio"].shape[0] >0:

        st.markdown("<h2 style='text-align:center'>Consolidated Portfolio Holdings</h2>", unsafe_allow_html=True)
       
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Scheme Type Distribution")

            # display donut chart
            donut = make_donut('portfolio')
            st.altair_chart(donut, use_container_width=True)
            
           
        with c2:
            
            st.subheader("Value by scheme type")

            # display donut chart
            donut = make_donut('value')
            st.altair_chart(donut, use_container_width=True)
        
        c1, c2 = st.columns(spec=[0.52, 0.48])

        with c1:
            # make the heading at center 
            st.subheader("Portfolio Holdings by Sector")
            # make donut chart
            donut2 = make_donut('sector_value')
            st.altair_chart(donut2, use_container_width=True)
        
        
        with c2:

            # from consolidated holdings get the top companies
            # get top 10 companies by value
            top_companies = get_top_companies()
            # reset index
            top_companies.reset_index(drop=True, inplace=True)

            # set index to start from 1
            top_companies.index = top_companies.index + 1

            # rename the columns
            top_companies.rename(columns={'index': 'Rank', 'company_name': 'Company', 'percent_value': '% of Total'}, inplace=True)

            # create a table in steamlit
            st.subheader("Top 10 Companies by Value")

            # convert the dataframe to a table
            st.dataframe(top_companies,hide_index=True)

        c1, c2 = st.columns(2)

        with c1:

            st.subheader("Sector Holdings of Scheme")
            # select scheme for analysis
            scheme_name = st.selectbox("Select Scheme", st.session_state["portfolio"]["Scheme Name"].unique())

            # Check if a scheme is selected
            if scheme_name is not None:
                # update session state to selected

                st.session_state["scheme"] = scheme_name

                # get holdings for the scheme
                
                hold_df = get_scheme_holdings()
                
                # set session state
                st.session_state["scheme_holdings"] = hold_df
                
                # make donut chart
                donut2 = make_donut('scheme')
                st.altair_chart(donut2, use_container_width=True)


          

# Call the main function
if __name__ == "__main__":
    main()
