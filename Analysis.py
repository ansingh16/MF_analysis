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
        input_df = st.session_state["select_portfolio"]
        # Calculate category counts
        category_counts = input_df['Scheme Category Name'].value_counts().reset_index()
        category_counts.columns = ['Scheme Category Name', 'count']
        # Create a donut chart
        donut = alt.Chart(category_counts).mark_arc(innerRadius=20).encode(
            theta="count",
            color="Scheme Category Name:N",
        )
        return donut
    
    elif type=="value":
        mf_portfolio = st.session_state["select_portfolio"]

        
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
    
    elif type=="scheme":
        input_df = st.session_state["scheme_holdings"]

        # Calculate category counts
        category_counts = input_df['sector_name'].value_counts().reset_index()
        category_counts.columns = ['sector_name', 'count']
        # Create a donut chart
        donut = alt.Chart(category_counts).mark_arc(innerRadius=20).encode(
            theta="count",
            color="sector_name:N",
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

    hold_df = scheme_df.loc[scheme_df['Scheme Name'] == st.session_state.scheme_name]

    return hold_df



@st.cache_data
def get_consolidated_holdings(mf_url,mf_unit):
    """
    Function to get consolidated holdings from all MF portfolio
    """
 
    url = requests.get(mf_url)
    # scrape url
    soup = BeautifulSoup(url.text, 'html.parser')

    # get scheme name
    scheme_name = soup.find_all('title')[0].get_text().split('-')[0].strip()

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
    hold_df['Scheme Name'] = scheme_name
    hold_df['NAV'] = float(NAV)
    hold_df['Units'] = mf_unit
    hold_df['Scheme Category'] = category + " - " + subcategory
    # hold_df['Scheme Sub-Category'] = subcategory

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
        hold_df = hold_df[['Scheme Name','Scheme Category','company_name','sector_name','corpus_per','NAV','Units']]
    
    return hold_df



# Function to load data
@st.cache_data
def analyze_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        # Read the uploaded file into a pandas DataFrame
        df = pd.read_csv(uploaded_file)
        return df




#     st.success("Entry added successfully.")


def add_portfolio_entry(scheme_url, units):
    # Read URL to get scheme name, NAV, category, and subcategory
    url_text = requests.get(scheme_url)
    soup = BeautifulSoup(url_text.text, 'html.parser')
    
    # Get the scheme name
    scheme_name = soup.find_all('title')[0].get_text().split('-')[0].strip()
    
    # Find the script tag with the specific ID
    script_tag = soup.find('script', id='__NEXT_DATA__')
    
    # Extract the JSON data from the script tag content
    json_data = json.loads(script_tag.contents[0])
    
    # Get NAV
    td_tag = soup.find_all('td',class_="fd12Cell contentPrimary bodyLargeHeavy")[0]
    value = td_tag.get_text(strip=True)
    NAV = float(re.search(r'₹([\d.]+)', value).group(1))
    
    # Get category and subcategory
    category = json_data['props']['pageProps']['mf']['category']
    subcategory = json_data['props']['pageProps']['mf']['sub_category']
    
    # Add entry to the list of inputs
    st.session_state.portfolio.append({"Scheme Name": scheme_name, "Units": float(units), 
                                       "NAV": NAV, "Scheme Category Name": category + " - " + subcategory, 
                                       "Scheme URL": scheme_url, 'Checkbox': True})

def check_ckbox():

    for i, input_data in enumerate(st.session_state.portfolio):
        checkbox_key = f"checkbox_{i}"
        units_key = f"units_{i}"

        scheme_name = input_data['Scheme Name']
        
        # Place checkbox and text input side by side using columns layout
        col1, col2 = st.sidebar.columns([1, 1])

        input_data['Checkbox'] = col1.checkbox(label=f"{scheme_name}", key=checkbox_key, value=input_data['Checkbox'])
        input_data['Units'] = col2.text_input(label="Units", key=units_key, value=input_data['Units'])
    
    
    # Filter out unchecked entries and update the DataFrame
    portfolio = pd.DataFrame([input_data for input_data in st.session_state.portfolio if input_data['Checkbox']])

    portfolio['Units'] = portfolio['Units'].astype(float)

    return portfolio

def scheme_sector_donut():

    # select scheme for analysis
    scheme_name = st.selectbox("Select Scheme", st.session_state["select_portfolio"]["Scheme Name"].unique())

    # Check if a scheme is selected
    if scheme_name is not None:
            # update session state to selected

            # get url from scheme_name
            scheme_url = st.session_state["select_portfolio"].loc[st.session_state["select_portfolio"]["Scheme Name"] == scheme_name,"Scheme URL"].values[0]

            url = requests.get(scheme_url)
            # scrape url
            soup = BeautifulSoup(url.text, 'html.parser')

            # get scheme name
            scheme_name = soup.find_all('title')[0].get_text().split('-')[0].strip()

            # Find the script tag with the specific ID
            script_tag = soup.find('script', id='__NEXT_DATA__')

            # Extract the JSON data from the script tag content
            json_data = json.loads(script_tag.contents[0])

            # get holdings
            holdings = json_data['props']['pageProps']['mf']['holdings']

            hold_df = pd.DataFrame(holdings)

                    
            # set session state
            st.session_state["scheme_holdings"] = hold_df
                    
            # make donut chart
            donut2 = make_donut('scheme')
            st.altair_chart(donut2, use_container_width=True)


def portfolio_plots():

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


def main():
    st.title("Mutual Fund Portfolio Analysis")

    # Initialize session state variables if not already initialized
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    if 'select_portfolio' not in st.session_state:
        st.session_state.select_portfolio = None
    if 'consol_holdings' not in st.session_state:
        st.session_state.consol_holdings = None
    if 'scheme_name' not in st.session_state:
        st.session_state.scheme_name = None

    # Sidebar input fields
    scheme_url = st.sidebar.text_input("Enter Scheme URL:")
    units = st.sidebar.text_input("Enter Units:")
    
    st.sidebar.header('OR')

    st.sidebar.header("Upload CSV File")

    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        # Read the uploaded file into a pandas DataFrame
        df = pd.read_csv(uploaded_file)
        for row in df.iterrows():
            scheme_url = row['Scheme URL']
            units = row['Units']
            add_portfolio_entry(scheme_url, units)

    # Check if add button is pressed
    if st.sidebar.button("Add"):
        if scheme_url and units:
            # Call the function to add the entry
            add_portfolio_entry(scheme_url, units)
    

    # Display entries with checkboxes in the sidebar
    st.sidebar.subheader("Entries:")
    
    # check which checkboxes are checked
    portfolio = check_ckbox()

    if not portfolio.empty:
        # change Units to float
        # save session state
        st.session_state["select_portfolio"] = portfolio

        st.subheader("Sector Holdings of Scheme")
        scheme_sector_donut()

    
    # Display the portfolio dataframe
    if st.sidebar.button("Analyze"):
       
        # get consolidated holdings
        all_url = st.session_state.select_portfolio['Scheme URL'].unique()
        all_units = st.session_state.select_portfolio['Units'].unique()
                    
        with st.spinner("Calculating Consolidated Holdings..."):
                            
            with Pool.Pool(4) as p:

                # use starmap to run in parallel on all urls
                consol_holdings_list = p.starmap(get_consolidated_holdings, zip(all_url,all_units))
                
                # concat the list of dataframes into a single dataframe
                consol_holdings = pd.concat(consol_holdings_list, ignore_index=True)

                # consolidated holdings
                st.session_state["consol_holdings"] = consol_holdings


        st.markdown("<h2 style='text-align:center'>Consolidated Portfolio Holdings</h2>", unsafe_allow_html=True)

        # make plots for a portfolio
        portfolio_plots()
        

          

# Call the main function
if __name__ == "__main__":
    main()
