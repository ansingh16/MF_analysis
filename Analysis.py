import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import altair as alt

# session state for uploaded file
if "file" not in st.session_state:
    st.session_state["file"] = None

# tracking function
def upload_file():
    if uploaded_file is not None:
        st.session_state["file"] = "uploaded"
    else:
        st.session_state["file"] = None

st.set_page_config(
    page_title="Mutual Fund Analysis",
    layout="wide",
    initial_sidebar_state="expanded")


def make_donut(input_df):
    # Rename columns for clarity
    category_counts = input_df['Scheme Category Name'].value_counts().reset_index()
    # Rename columns for clarity
    category_counts.columns = ['category', 'count']
    donut = alt.Chart(category_counts).mark_arc(innerRadius=50).encode(
        theta="count",
        color="category:N",
    )

    return donut

# get holdings
def get_holdings(input_df,scheme_name):
    """
    This function sends a GET request to a specific URL, parses the HTML using BeautifulSoup, 
    finds a script tag with a specific ID, extracts JSON data from the script tag content, and 
    retrieves holdings and creates a pandas DataFrame. No parameters are passed and no return 
    type is specified.
    """
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

# sidebar
with st.sidebar:
    st.title('Mutual Fund Dashboard')
    
    # get uploaded file
    uploaded_file = st.sidebar.file_uploader("Upload your CSV", type=["csv"], on_change=upload_file)

    if st.session_state["file"] == "uploaded":
        try:

            # read csv
            df = pd.read_csv(uploaded_file)

            # get selected scheme
            selected_scheme = st.selectbox("Select Scheme", df["Scheme Name"].unique())

            # get holdings
            hold_i = get_holdings(df,selected_scheme)

        except Exception as e:
            st.error(f"Error: {e}")


with st.container():
    if st.session_state["file"] == "uploaded":
        st.header("Portfolio Holdings")
        if st.session_state["file"] == "uploaded":
            donut = make_donut(df)
            st.altair_chart(donut, use_container_width=True)
