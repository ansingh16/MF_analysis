import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import altair as alt



def make_donut(type):

    if type=="portfolio":
        input_df = st.session_state["portfolio"]
        # Calculate category counts
        category_counts = input_df['Scheme Category Name'].value_counts().reset_index()
        category_counts.columns = ['category', 'count']
        # Create a donut chart
        donut = alt.Chart(category_counts).mark_arc(innerRadius=20).encode(
            theta="count",
            color="category:N",
        )
        return donut
        
    elif type=="scheme":
        input_df = st.session_state["scheme_holdings"]
        # Calculate category counts
        category_counts = input_df[['company_name','corpus_per']]
        # Create a donut chart
        donut = alt.Chart(category_counts).mark_arc(innerRadius=20).encode(
            theta="corpus_per",
            color="company_name:N",
        )
        return donut
    


   

# get holdings
@st.cache_data
def get_holdings():
    """
    This function sends a GET request to a specific URL, parses the HTML using BeautifulSoup, 
    finds a script tag with a specific ID, extracts JSON data from the script tag content, and 
    retrieves holdings and creates a pandas DataFrame. No parameters are passed and no return 
    type is specified.
    """
    input_df = st.session_state["portfolio"]
    scheme_name = st.session_state["scheme"]

    url = requests.get(input_df.loc[input_df['Scheme Name'] == scheme_name,'scheme_url'].values[0])
    soup = BeautifulSoup(url.text, 'html.parser')

    # Find the script tag with the specific ID
    script_tag = soup.find('script', id='__NEXT_DATA__')

    # Extract the JSON data from the script tag content
    json_data = json.loads(script_tag.contents[0])

    # get holdings
    holdings = json_data['props']['pageProps']['mf']['holdings']

    # get pandas
    hold_df = pd.DataFrame(holdings)

    return hold_df



def get_consolidated_holdings():

    all_schemes = st.session_state["portfolio"]['Scheme Name'].unique()
    input_df = st.session_state["portfolio"]

    consol_df = pd.DataFrame()
    for scheme in all_schemes:
        url = requests.get(input_df.loc[input_df['Scheme Name'] == scheme,'scheme_url'].values[0])
        soup = BeautifulSoup(url.text, 'html.parser')

        # Find the script tag with the specific ID
        script_tag = soup.find('script', id='__NEXT_DATA__')

        # Extract the JSON data from the script tag content
        json_data = json.loads(script_tag.contents[0])

        # get holdings
        holdings = json_data['props']['pageProps']['mf']['holdings']

        # get pandas
        hold_df = pd.DataFrame(holdings)
        
        # hold_df = hold_df[['company_name','sector_name','corpus_per']]

        consol_df = pd.concat([hold_df, consol_df], ignore_index=True)

    consol_df = consol_df[['company_name','sector_name','corpus_per']]
    return consol_df

# Function to load data
@st.cache_data
def analyze_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        # Read the uploaded file into a pandas DataFrame
        df = pd.read_csv(uploaded_file)
        return df
def main():
    st.title("Analyse Mutual Fund Portfolio")

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

                consol_holdings = get_consolidated_holdings()
                # consolidated holdings
                st.session_state["consol_holdings"] = consol_holdings

    # Display the contents of the uploaded file
    if st.session_state["portfolio"] is not None:
        st.subheader("Scheme Type Distribution")
    
        # display donut chart
        donut = make_donut('portfolio')
        st.altair_chart(donut, use_container_width=True)
        
        # select scheme for analysis
        scheme_name = st.selectbox("Select Scheme", st.session_state["portfolio"]["Scheme Name"].unique())

        # Check if a scheme is selected
        if scheme_name is not None:
            # update session state to selected

            st.session_state["scheme"] = scheme_name

            st.subheader("Portfolio Holdings")
            hold_df = get_holdings()
            
            
            st.session_state["scheme_holdings"] = hold_df

            donut2 = make_donut('scheme')
            st.altair_chart(donut2, use_container_width=True)
        
            st.subheader("Consolidated Holdings")
            # st.dataframe(st.session_state["consol_holdings"])


# Call the main function
if __name__ == "__main__":
    main()
