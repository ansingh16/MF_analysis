import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import altair as alt
import multiprocessing.pool as Pool
import re
from streamlit_navigation_bar import st_navbar
from pathlib import Path
from yahooquery import Ticker
import mstarpy

def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()

st.set_page_config(initial_sidebar_state="expanded")


 # Initialize session state variables if not already initialized

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'select_portfolio' not in st.session_state:
    st.session_state.select_portfolio = None
if 'consol_holdings' not in st.session_state:
    st.session_state.consol_holdings = None
if 'scheme_name' not in st.session_state:
    st.session_state.scheme_name = None
if 'selected_schemes' not in st.session_state:
    st.session_state.selected_schemes = None       
if 'update' not in st.session_state:
    st.session_state.selected_schemes = None
if 'ticker_data' not in st.session_state:
    st.session_state.ticker_data = None

styles_nav = {
        "nav": {
             "width": "70%",
            "background-color": "teal",
            "float": "right",
            "overflow": "hidden",
        },
        "span": {
            "border-radius": "0.5rem",
            "padding": "0.4375rem 0.625rem",
            "margin": "0 0.125rem",
        },
        "active": {
            "background-color": "rgba(255, 255, 255, 0.25)",
        },
        "hover": {
            "background-color": "rgba(255, 255, 255, 0.35)",
        }
    }


@st.cache_data
def donut_portfolio(consol_holdings):
    # Calculate category counts
    category_counts = consol_holdings['Scheme Category'].value_counts().reset_index()
    category_counts.columns = ['Scheme Category', 'count']
    # Create a donut chart
    donut = alt.Chart(category_counts).mark_arc(innerRadius=20).encode(
            theta="count",
            color="Scheme Category:N",
        )
    return donut

@st.cache_data
def donut_value(mf_portfolio):
    
        
    # Calculate current value in schemes
    scheme_value = mf_portfolio['Units'] * mf_portfolio['NAV']
    # get total value
    total_value = scheme_value.sum()
    mf_portfolio['Fraction Value'] = (scheme_value / total_value)*100

    # Group by Scheme Category Name and calculate the sum of the Fraction Value
    category_value = mf_portfolio.groupby('Scheme Category')['Fraction Value'].sum().reset_index()

    # Create the donut chart
    donut = alt.Chart(category_value).mark_arc(innerRadius=20).encode(
            color='Scheme Category:N',
            theta='Fraction Value',
            tooltip=['Scheme Category', alt.Tooltip('Fraction Value:Q', title='Percentage Allocated', format='.2f')]
        )
        
        
    return donut

@st.cache_data
def donut_sector_value(consol_df):
    consol_df = st.session_state["consol_holdings"]
    # Calculate current value in schemes
    all_scheme_value = consol_df['Units'] * consol_df['NAV']
    # get total value
    total_value = all_scheme_value.sum()
    consol_df['Fraction Value'] = (all_scheme_value / total_value)*100

    # Group by Scheme Category Name and calculate the sum of the Fraction Value
    category_value = consol_df.groupby('Sector')['Fraction Value'].sum().reset_index()

    # Create the donut chart
    donut = alt.Chart(category_value).mark_arc(innerRadius=20).encode(
            color='Sector:N',
            theta='Fraction Value',
            tooltip=['Sector', alt.Tooltip('Fraction Value:Q', title='Percentage Allocated', format='.2f')]
        ).mark_arc(innerRadius=20,outerRadius=80)
        
        
    return donut

@st.cache_data
def donut_scheme_holding(holdings_df):
    
    # change name of column to Sector
    holdings_df.rename(columns={'sector_name':'Sector'}, inplace=True)
    # Calculate category counts
    category_counts = holdings_df['Sector'].value_counts().reset_index()
    category_counts.columns = ['Sector', 'count']
    # Create a donut chart
    donut = alt.Chart(category_counts).mark_arc(innerRadius=20).encode(
            theta="count",
            color="Sector:N",
        )
    return donut

@st.cache_data
def get_scheme_hold(portfolio,scheme_name):
    
    scheme_url = portfolio.loc[portfolio["Scheme Name"] == scheme_name,"Scheme URL"].values[0]

    url = requests.get(scheme_url)
    # scrape url
    soup = BeautifulSoup(url.text, 'html.parser')
    
    # Find the script tag with the specific ID
    script_tag = soup.find('script', id='__NEXT_DATA__')

    # Extract the JSON data from the script tag content
    json_data = json.loads(script_tag.contents[0])

    # get holdings
    holdings = json_data['props']['pageProps']['mf']['holdings']

    hold_df = pd.DataFrame(holdings)

    return hold_df

@st.cache_data
def compare_schemes(portfolio, scheme1, scheme2):
   

    portfolio1 = get_scheme_hold(portfolio, scheme1)
    portfolio2 = get_scheme_hold(portfolio, scheme2)

    portfolio1['Scheme Name'] = scheme1
    portfolio2['Scheme Name'] = scheme2

    portfolio1.rename(columns={'sector_name':'Sector', 'company_name':'Company', 'corpus_per':'Percent Contribution'}, inplace=True)
    portfolio2.rename(columns={'sector_name':'Sector', 'company_name':'Company', 'corpus_per':'Percent Contribution'}, inplace=True)

    # print(portfolio1)
    # print(portfolio2)

    df = pd.concat([portfolio1, portfolio2], axis=0)


    df_grouped = df.groupby(['Scheme Name', 'Sector']).agg({
        'Percent Contribution': 'sum',
        'Company': lambda x: ', '.join(set(x))
    }).reset_index()

    # print(df_grouped)

    chart = alt.Chart(df_grouped).mark_bar().encode(
        x='Sector:N',
        y='sum(Percent Contribution):Q',
        color='Scheme Name:N',
        tooltip=['Sector:N', 'Company:N'],
        xOffset=alt.XOffset("Scheme Name:N")
    ).properties(
        title='Sectorwise Contribution of Schemes',
        width=600,
        height=400
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        grid=False
    ).configure_legend(
        labelFontSize=12
    )

    return chart


    


@st.cache_data
def get_top_companies():
    """
    Function to get top companies
    """
    consol_df = st.session_state["consol_holdings"]

    # get value invested in a company
    consol_df['company_value']  = consol_df['Units'] * consol_df['NAV']*consol_df['Percent Contribution']
    
    # percent invested in a company with respect to total value of all companies
    consol_df['Percentage by Value'] = (consol_df['company_value']/consol_df['company_value'].sum())*100

    # group by company_name and calculate the sum of the value and sort in descending order
    top_companies = consol_df.groupby('Company')['Percentage by Value'].sum().reset_index().sort_values(by='Percentage by Value', ascending=False)

    comapny_details = []
    # get all tickers and check the companies
    for company in top_companies['Company'].head(10):
        
        if company.upper() in st.session_state.ticker_data['name'].values:
            ticker = st.session_state.ticker_data.loc[st.session_state.ticker_data['name'] == company.upper(),'tradingsymbol'].values[0]
            ticker_yf = Ticker(ticker+'.NS') 
            fin_data_dict = ticker_yf.financial_data

            comapny_details.append(fin_data_dict[ticker+'.NS'])

    comapny_details = pd.DataFrame(comapny_details)
    return top_companies.head(10), comapny_details


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
    hold_df['Units'] = float(mf_unit)
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

        hold_df.columns = ['Scheme Name','Scheme Category', 'Company', 'Sector', 'Percent Contribution', 'NAV', 'Units']
    
    return hold_df


# Function to load data
def analyze_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        # Read the uploaded file into a pandas DataFrame
        df = pd.read_csv(uploaded_file)
        return df


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

    
    return portfolio

            

def portfolio_plots(consol_holdings):

    c1, c2 = st.columns(2)

    with c1:
            
            st.subheader("Scheme Type Distribution")

            # display donut chart
            donut = donut_portfolio(consol_holdings)
            st.altair_chart(donut,use_container_width=True)
                
           
    with c2:
           
            st.subheader("Scheme Value Distribution")
            # display donut chart
            donut = donut_value(consol_holdings)
            st.altair_chart(donut,use_container_width=True)




    c1, c2 = st.columns(spec=[0.52, 0.48])

    with c1:
            # make the heading at center 
            st.subheader("Portfolio Holdings by Sector")
            # make donut chart
            donut2 = donut_sector_value(consol_holdings)
            st.altair_chart(donut2,use_container_width=True)
            
        
    with c2:

            # from consolidated holdings get the top companies
            # get top 10 companies by value
            top_companies, comapny_details = get_top_companies()
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
    
    st.markdown("---")
    st.dataframe(comapny_details)

def nav_scheme_sector(portfolio):
     
    # check which checkboxes are checked
    
    if not portfolio.empty:

        # change Units to float
        portfolio['Units'] = portfolio['Units'].astype(float)

        
        
        st.subheader("Sector Holdings of Scheme")

        # select scheme for analysis
        scheme_name = st.selectbox("Select Scheme", portfolio["Scheme Name"].unique())

        # get url from scheme_name
        scheme_url = portfolio.loc[portfolio["Scheme Name"] == scheme_name,"Scheme URL"].values[0]

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
        donut2 = donut_scheme_holding(hold_df)
        st.altair_chart(donut2,use_container_width=True)




def nav_scheme_compare(portfolio):
    

    if not portfolio.empty:

        if portfolio.shape[0]>=2:
             
            st.markdown("<h3 style='text-align:center'>Scheme Comparison</h3>", unsafe_allow_html=True)

            # Display the dataframe with checkboxes for selection
                        
            # Display the multiselect widget to select schemes
            selected_schemes = st.multiselect('Select 2 schemes to compare:', portfolio["Scheme Name"].unique(), default=[], max_selections=3)

            # Ensure only two schemes are selected
            if len(selected_schemes) > 2:
                st.warning('Please select only 2 schemes.')
            elif len(selected_schemes) == 2:
                
                if st.button("Compare"):
                    chart = compare_schemes(portfolio,selected_schemes[0],selected_schemes[1])

                    st.altair_chart(chart,use_container_width=True)
           

def nav_portfolio(portfolio):
    
    if not portfolio.empty:
            
                if portfolio.shape[0] >=1:
                    # get consolidated holdings
                    all_url = portfolio['Scheme URL'].unique()
                    all_units = portfolio['Units'].unique()
                        
                    with st.spinner("Calculating Consolidated Holdings..."):
                        consol_holdings_list = []             
                        for url, units in zip(all_url, all_units):
                                # get consolidated holdings

                                # use starmap to run in parallel on all urls
                                holdings = get_consolidated_holdings(url,units)
                                
                                # append list
                                consol_holdings_list.append(holdings)

                        # concat the list of dataframes into a single dataframe
                        consol_holdings = pd.concat(consol_holdings_list, ignore_index=True)

                        # consolidated holdings
                        st.session_state["consol_holdings"] = consol_holdings


                st.markdown("<h2 style='text-align:center'>Consolidated Portfolio Holdings</h2>", unsafe_allow_html=True)

                # make plots for a portfolio
                portfolio_plots(st.session_state.consol_holdings)
                
def nav_about():
    intro_markdown = read_markdown_file("README.md")
    st.markdown(intro_markdown, unsafe_allow_html=True)


def nav_scheme_suggest():
     
    # read the data from the csv file
    all_schemes = pd.read_csv('all_schemes.csv')

    # display multiselect widget
    
         


def main():

    # all tickers 
        
    all_tickers = pd.read_csv('all_tickers_india.csv',usecols=['instrument_key','tradingsymbol','name'])

    st.session_state.ticker_data = all_tickers

    pages = ["About","Scheme Distribution", "Scheme Compare", "Portfolio Analysis","Scheme Suggest"]
    
    
    # Add entry to the list of inputs
    with st.sidebar:

        # set App Name
        st.markdown("<h1 style='text-align: center;'>Mutual Fund Analyzer</h1>", unsafe_allow_html=True)
        #add logo at the center
        
        left_co, cent_co,last_co = st.columns(3)
        with cent_co:
            st.image('./images/logo.jpeg', use_column_width=True)
        

        st.markdown('---')

        st.markdown("<h2 style='text-align: center;'>Portfolio Dashboard</h2>", unsafe_allow_html=True)



        # # Sidebar input fields
        # scheme_url = st.text_input("Enter Groww Scheme URL:")
        # units = st.text_input("Enter Units:")
    
        

        # if st.button("Add", key="add"):
        #         if scheme_url and units:
        #             # Call the function to add the entry
        #             add_portfolio_entry(scheme_url, units)
        response = mstarpy.search_funds(term="Quant Momentum", field=["Name",'fundShareClassId'], country="in", pageSize=100, currency="INR")
        response_df = pd.DataFrame(response)
        

        st.data_editor(
        response_df,
        column_config={
            "favorite": st.column_config.CheckboxColumn(
                "Your favorite?",
                help="Select your **favorite** widgets",
                default=False,
            )
        },
        disabled=["widgets"],
        hide_index=True,
)
        

        st.header('OR')

        st.header("Upload CSV File")
        st.info("Please upload a CSV file with the following columns: 'Scheme URL', 'Units'")

        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

        if st.button("Add file",key="add_csv"):
            if uploaded_file is not None:
                # Read the uploaded file into a pandas DataFrame
                df = pd.read_csv(uploaded_file)
                
                for scheme_url, units in zip(df['Scheme URL'], df['Units']):
                    # scheme_url = row['Scheme URL']
                    # units = row['Units']
                    add_portfolio_entry(scheme_url, units)


        st.markdown('---')
            
        # Display entries with checkboxes in the sidebar
        st.markdown("<h1 style='text-align: center;'>Schemes Entries</h1>", unsafe_allow_html=True)
        
         # check which checkboxes are checked
        portfolio = check_ckbox()

    # Render the navigation bar
    navigation = st_navbar(pages, styles=styles_nav,selected='About')



    
    if navigation == 'About':
        nav_about()
    elif navigation == 'Scheme Distribution':
        nav_scheme_sector(portfolio)
    elif navigation == 'Scheme Compare':
        nav_scheme_compare(portfolio)
    elif navigation == 'Portfolio Analysis':
        nav_portfolio(portfolio)
    elif navigation == 'Scheme Suggest':
        nav_scheme_suggest()
    

        
        

          

# Call the main function
if __name__ == "__main__":
    main()
