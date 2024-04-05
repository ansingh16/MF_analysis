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
    


# get holdings
def get_scheme_holdings():
    """
    This function sends a GET request to a specific URL, parses the HTML using BeautifulSoup, 
    finds a script tag with a specific ID, extracts JSON data from the script tag content, and 
    retrieves holdings and creates a pandas DataFrame. No parameters are passed and no return 
    type is specified.
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

    NAV= re.search(r'₹([\d.]+)', value).group(1)

    # get pandas
    hold_df = pd.DataFrame(holdings)
    hold_df['Scheme Name'] = schemei
    hold_df['NAV'] = float(NAV)
    hold_df['Units'] = Units
        
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



def main():
    st.title("Analyze Mutual Fund Portfolio")

    st.sidebar.header("Upload CSV File")

    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

    # Initialize session state if not already initialized
    if "portfolio" not in st.session_state:
        st.session_state["portfolio"] = None

    # Button to Analyze Uploaded File
    if uploaded_file is not None:
        if st.sidebar.button("Analyze"):
            # Perform analysis on the uploaded file
            df = analyze_uploaded_file(uploaded_file)
            if df is not None:
                # Update session state with analyzed DataFrame
                st.session_state["portfolio"] = df

                # get consolidated holdings


                all_schemes = df['Scheme Name'].unique()

                
                
                with Pool.Pool(4) as p:

                    # use map to run in parallel on all schemes
                    consol_holdings_list = p.map(get_consolidated_holdings, all_schemes)

                    # concat the list of dataframes into a single dataframe
                    consol_holdings = pd.concat(consol_holdings_list, ignore_index=True)



                # consolidated holdings
                
                st.session_state["consol_holdings"] = consol_holdings

    st.subheader("Consolidated Portfolio Holdings")
    # Display the contents of the uploaded file
    if st.session_state["portfolio"] is not None:
       
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
        
        st.subheader("Porfolio Holdings by Sector")
        # make donut chart
        donut2 = make_donut('sector_value')
        st.altair_chart(donut2, use_container_width=True)
        
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
