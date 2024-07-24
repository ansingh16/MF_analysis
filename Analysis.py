import streamlit as st
import pandas as pd
import altair as alt
from streamlit_navigation_bar import st_navbar
from pathlib import Path
from yahooquery import Ticker
import mstarpy
import datetime
from multiprocessing import Pool
from mstarpy import search_filter
from mstarpy import filter_universe
from mstarpy import search_funds
from rapidfuzz import process
from thefuzz import process
import seaborn as sns
import matplotlib.pyplot as plt

def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()

st.set_page_config(initial_sidebar_state="expanded")


 # Initialize session state variables if not already initialized

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame()
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
if 'top_companies' not in st.session_state:
    st.session_state.top_companies = None
if 'add_fund' not in st.session_state:
    st.session_state.add_fund = None

styles_nav = {
        "nav": {
             "width": "70%",
            "background-color": "teal",
            "float": "right",
            "overflow": "hidden"
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



# Function to find closest match
def get_closest_match(input_string, possible_matches):
    closest_match = process.extractOne(input_string, possible_matches)
    return closest_match if closest_match else None


@st.cache_data
def donut_portfolio(consol_holdings):

    # print(consol_holdings['Scheme Category'])
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
    
    # print(mf_portfolio['Units'], mf_portfolio['NAV'])
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
    # consol_df = st.session_state["consol_holdings"]

    # print(consol_df.columns)

    # Calculate current value in schemes
    all_scheme_value = consol_df['Units'] * consol_df['NAV']
    # get total value
    total_value = all_scheme_value.sum()
    consol_df['Fraction Value'] = (all_scheme_value / total_value)*100

    # consol_df['Sector'] = 

    consol_df.rename(columns={'sector':'Sector'}, inplace=True)

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
    holdings_df.rename(columns={'holdingType':'Sector'}, inplace=True)
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
    
    fund_df = portfolio.loc[portfolio["Scheme Name"] == scheme_name,"fund_data"].values[0]

    # get holdings
    holdings = fund_df.holdings(holdingType="all")


    return holdings



@st.cache_data
def compare_schemes(portfolio, scheme1, scheme2):
   

    portfolio1 = get_scheme_hold(portfolio, scheme1)
    portfolio2 = get_scheme_hold(portfolio, scheme2)

    portfolio1['Scheme Name'] = scheme1
    portfolio2['Scheme Name'] = scheme2

    portfolio1.rename(columns={'sector':'Sector', 'securityName':'Company', 'weighting':'Percent Contribution'}, inplace=True)
    portfolio2.rename(columns={'sector':'Sector', 'securityName':'Company', 'weighting':'Percent Contribution'}, inplace=True)

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

    consol_df.rename(columns={'sector':'Sector', 'securityName':'Company', 'weighting':'Percent Contribution'}, inplace=True)

    consol_df = consol_df.dropna(subset=['Percent Contribution'])
        
    # fill None in sector column with holdingType
    consol_df['Sector'] = consol_df['Sector'].fillna(consol_df['holdingType'])


    # get value invested in a company
    consol_df['company_value']  = consol_df['Units'] * consol_df['NAV']*consol_df['Percent Contribution']
    
    # percent invested in a company with respect to total value of all companies
    consol_df['Percentage by Value'] = (consol_df['company_value']/consol_df['company_value'].sum())*100

    # group by company_name and calculate the sum of the value and sort in descending order
    top_companies = consol_df.groupby(['Company', 'Sector'])['Percentage by Value'].sum().reset_index().sort_values(by='Percentage by Value', ascending=False)

    # comapny_details = []
    # get all tickers and check the companies
    # for company in top_companies['Company'].head(10):
        
        # if company.upper() in st.session_state.ticker_data['name'].values:
        #     ticker = st.session_state.ticker_data.loc[st.session_state.ticker_data['name'] == company.upper(),'tradingsymbol'].values[0]
        #     ticker_yf = Ticker(ticker+'.NS') 
        #     fin_data_dict = ticker_yf.financial_data

        #     comapny_details.append(fin_data_dict[ticker+'.NS'])

    # comapny_details = pd.DataFrame(comapny_details)
    return top_companies



# Function to load data
def analyze_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        # Read the uploaded file into a pandas DataFrame
        df = pd.read_csv(uploaded_file)
        return df


def add_portfolio_entry(fund_data, units, nav):
    name = fund_data.name
    category_name = fund_data.allocationMap()['categoryName']

    # Check if session_state.portfolio is empty
    if st.session_state.portfolio.empty:
        st.session_state.portfolio = pd.DataFrame([{"Scheme Name": name, "Units": float(units), "NAV": float(nav), "fund_data": fund_data, "Scheme Category": category_name, 'Checkbox': True}])
    else:
        # Append the new entry to the existing DataFrame
        st.session_state.portfolio.loc[len(st.session_state.portfolio.index)] = [name, float(units), float(nav), fund_data, category_name, True]


def process_fund(scheme_unit):
    search_scheme, units = scheme_unit
    response = mstarpy.search_funds(term=search_scheme, field=["Name", "fundShareClassId", "SectorName"], country="in", pageSize=20)
    
    
    if response:
        result = response[0]
        fund_data = mstarpy.Funds(term=result['Name'], country="in")
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=3)
        history = fund_data.nav(start_date=yesterday, end_date=today, frequency="daily")

        if history:
            df_history = pd.DataFrame(history)
            nav = df_history['nav'].iloc[-1]

            return (fund_data, units, nav)
    return None

def check_ckbox():

        # print(st.session_state.portfolio)

        input_data = st.session_state.portfolio
        

        for i in range(st.session_state.portfolio.shape[0]):
            checkbox_key = f"checkbox_{i}"
            units_key = f"units_{i}"

            
            scheme_name = input_data['Scheme Name'].iloc[i]
            
            # Place checkbox and text input side by side using columns layout
            col1, col2 = st.sidebar.columns([1, 1])

           
            # set checkbox
            input_data['Checkbox'] = col1.checkbox(label=f"{scheme_name}", key=checkbox_key, value=input_data['Checkbox'].values[0])
            
            # set units
            input_data['Units'] = col2.text_input(label="Units", key=units_key, value=input_data['Units'].values[0])
        
        if st.session_state.portfolio.shape[0]>0:

            # Filter out unchecked entries and update the DataFrame
            input_data = input_data.loc[input_data['Checkbox'] == True]

        return input_data
             

            

def portfolio_plots(consol_df):

    consol_holdings = consol_df.dropna(subset=['weighting'])
        
    # fill None in sector column with holdingType
    consol_holdings['sector'] =consol_holdings['sector'].fillna(consol_holdings['holdingType'])


    # print("Here")
    # print(consol_holdings)

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

    # from consolidated holdings get the top companies
    # get top 10 companies by value
    top_companies = st.session_state.top_companies
    # reset index
    top_companies.reset_index(drop=True, inplace=True)
    # set index to start from 1
    top_companies.index = top_companies.index + 1
    # rename the columns
    top_companies.rename(columns={'index': 'Rank', 'company_name': 'Company', 'percent_value': '% of Total'}, inplace=True)

    # print(top_companies.columns)

    with c1:
            # make the heading at center 
            st.subheader("Portfolio Holdings by Sector")
            # make donut chart
            donut2 = donut_sector_value(consol_holdings)
            st.altair_chart(donut2,use_container_width=True)

            st.subheader("Search Company")

            # create search bar
            search_term = st.text_input(label="Search Company")

            
            if search_term:

                closest_match = get_closest_match(search_term, top_companies['Company'].tolist())

                if closest_match:
                    matched_name = closest_match[0]
                    score = closest_match[1]

                    # display closest match and its Percentage by Value
                    st.write(f'Closest match: {matched_name} (Score: {score})')
                    st.write(f'Percentage by Value: {top_companies[top_companies["Company"] == matched_name]["Percentage by Value"].values[0]:.2f}%')
                else:
                    st.write('No close match found.')

            
        
    with c2:

           
            # create a table in steamlit
            st.subheader("Top 10 Companies by Value")

            # convert the dataframe to a table
            for i, row in top_companies.head(15).iterrows():
                st.write(f" {row['Company']} ({row['Percentage by Value']:.2f}%)")
    
    st.markdown("---")
    
    # section for top companies in different sectors
    st.subheader("Top-Companies in different sectors")


    # Group top companies by sector
    top_companies_by_sector = top_companies.groupby('Sector').apply(lambda x: x.nlargest(10, 'Percentage by Value')).reset_index(drop=True)

    # Create a table in Streamlit for each sector and display the top 10 companies in each sector with Percent Contribution
    for sector in top_companies_by_sector['Sector'].unique():
        st.subheader(sector)
        top_companies_in_sector = top_companies_by_sector[top_companies_by_sector['Sector'] == sector]

        
        st.table(top_companies_in_sector[['Company', 'Percentage by Value']])

    # st.table(top_companies_by_sector)


    


# Function to process each scheme in parallel
def get_holdings(portfolio, scheme_name, units, nav):
    holdings = get_scheme_hold(portfolio, scheme_name)
    holdings['Units'] = float(units)
    holdings['NAV'] = nav
    holdings['Scheme Category'] = portfolio.loc[portfolio["Scheme Name"] == scheme_name, "Scheme Category"].values[0]
    holdings['Scheme Name'] = portfolio.loc[portfolio["Scheme Name"] == scheme_name, "Scheme Name"].values[0]
    return holdings




def nav_scheme_distribution(portfolio):
     
    # check which checkboxes are checked
    
    if not portfolio.empty:

        # change Units to float
        portfolio['Units'] = portfolio['Units'].astype(float)

        
        
        st.subheader("Sector Holdings of Scheme")

        # select scheme for analysis
        scheme_name = st.selectbox("Select Scheme", portfolio["Scheme Name"].unique())

        fund_df = portfolio.loc[portfolio["Scheme Name"] == scheme_name,"fund_data"].values[0]

        # get holdings
        holdings = fund_df.holdings(holdingType="all")

                    
        # set session state
        st.session_state["scheme_holdings"] = holdings
            
        # make donut chart
        donut2 = donut_scheme_holding(holdings)
        st.altair_chart(donut2,use_container_width=True)

        st.markdown("---")

        st.subheader("Holdings")

        scheme_holdings = get_scheme_hold(portfolio, scheme_name)

        scheme_holdings.rename(columns={'weighting':'Percent Contribution','securityName':'Company','sector':'Sector'}, inplace=True)

        scheme_holdings = scheme_holdings.dropna(subset=['Percent Contribution'])
        
        # fill None in sector column with holdingType
        scheme_holdings['Sector'] = scheme_holdings['Sector'].fillna(scheme_holdings['holdingType'])



        st.table(scheme_holdings[['Company', 'Sector', 'Percent Contribution']])


# Function to process the data and calculate the correlation matrix between schemes
@st.cache_data
def correlation(df):
    # Aggregate sector allocations by scheme
    sector_allocations = df.groupby(['Scheme Name', 'sector'])['weighting'].sum().reset_index()
    
    # Pivot the data to get schemes as rows and sectors as columns
    df_pivot = sector_allocations.pivot(index='Scheme Name', columns='sector', values='weighting').fillna(0)
    
    # Compute the correlation matrix between schemes
    correlation_matrix = df_pivot.T.corr()
    
    return correlation_matrix


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


        st.markdown("---")

        st.subheader("Correlation Between Schemes Based on Sector Allocations")

        # Ensure the DataFrame has the necessary columns
        if 'securityName' in st.session_state.consol_holdings.columns and 'sector' in st.session_state.consol_holdings.columns and 'weighting' in st.session_state.consol_holdings.columns and 'Scheme Name' in st.session_state.consol_holdings.columns:

            consol_holdings = st.session_state.consol_holdings.dropna(subset=['weighting'])
        
            # fill None in sector column with holdingType
            consol_holdings['sector'] =consol_holdings['sector'].fillna(consol_holdings['holdingType'])


            # Process data to get the correlation matrix
            correlation_matrix = correlation(consol_holdings)
            
            # Reset index for Altair compatibility
            correlation_matrix = correlation_matrix.reset_index().rename(columns={'index': 'Scheme Name'})
            correlation_matrix_melted = correlation_matrix.melt(id_vars='Scheme Name', var_name='Scheme Name ', value_name='Correlation')
            
            # in altair show correlation inside the heatmap
            
            # Create the heatmap using Altair
            base = alt.Chart(correlation_matrix_melted).encode(
                x='Scheme Name:O',
                y='Scheme Name :O'
            )

            heatmap = base.mark_rect().encode(
            color=alt.Color('Correlation:Q', scale=alt.Scale(domain=[-1, 1]))
            ).properties(
                width=600,
                height=600,
            )

            text = base.mark_text(baseline='middle').encode(
                text=alt.Text('Correlation:Q', format='.2f'),
                color=alt.condition(
                    alt.datum.Correlation > 0.5, 
                    alt.value('black'), 
                    alt.value('white')
                )
            )

            # Combine the heatmap and text
            chart = heatmap + text

            # Display the heatmap in Streamlit
            st.altair_chart(chart, use_container_width=True)


            


def nav_portfolio(portfolio):
    
    if not portfolio.empty:

               

                # get top companies
                st.session_state["top_companies"] = get_top_companies()

                st.markdown("<h2 style='text-align:center'>Consolidated Portfolio Holdings</h2>", unsafe_allow_html=True)
                
               
                # make plots for a portfolio
                portfolio_plots(st.session_state.consol_holdings)
                
def nav_about():
    intro_markdown = read_markdown_file("README.md")
    st.markdown(intro_markdown, unsafe_allow_html=True)


# Function to process each scheme


def main():
    
    # response = mstarpy.search_funds(term="", field=["Name",'fundShareClassId'], country="in", pageSize=100000, currency="INR")
    # df = pd.DataFrame(response)

    # df.to_parquet('mstar_funds.parquet')

    # all tickers 
        
    all_tickers = pd.read_csv('all_tickers_india.csv',usecols=['instrument_key','tradingsymbol','name'])

    st.session_state.ticker_data = all_tickers

    pages = ["About","Scheme Distribution", "Scheme Compare", "Portfolio Analysis"]
    
    
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


        # create search bar
        search_term = st.sidebar.text_input(label="Search", key=1)

        if search_term:

            # search for mutual funds
            response = mstarpy.search_funds(term=search_term, field=["Name"],country="in", pageSize=100000)
            # convert to dataframe
            response = pd.DataFrame(response)

            # get filtered options
            filtered_options = [option for option in response.Name if search_term.lower() in option.lower()]


            # Display the selectbox with filtered options
            selected_mutual_funds = st.selectbox('Select an option', filtered_options)


        
            if selected_mutual_funds != ' ':

                

                include_units = st.text_input(label="Units", key=2, value=1)
                if st.button("Add", key="add"):
                    # add screener
                    fund_data = mstarpy.Funds(term=selected_mutual_funds, country="in")

                    # today
                    today = datetime.date.today()
                    # yesterday
                    yesterday = today - datetime.timedelta(days=2)

                    #get historical data
                    history = fund_data.nav(start_date=yesterday,end_date=today, frequency="daily")
                    
                    
                    # if history is not empty
                    if len(history) > 0:
                        # with spinner:
                        df_history = pd.DataFrame(history)
                        nav = df_history['nav'].iloc[-1]

                        
                        add_portfolio_entry(fund_data, include_units,nav)
        


        st.header('OR')

                
        st.header("Upload CSV File")
        st.info("Please upload a CSV file with the following columns: 'Scheme Name', 'Units'")

        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        if st.button("Add file", key="add_csv"):
            if uploaded_file is not None:
                # Read the uploaded file into a pandas DataFrame
                input_portfolio = pd.read_csv(uploaded_file)

                schemes_units = list(zip(input_portfolio['Scheme Name'], input_portfolio['Units']))

                with Pool() as pool:
                    results = pool.map(process_fund, schemes_units)

                    
                for result in results:
                    if result:
                        fund_data, units, nav = result
                        add_portfolio_entry(fund_data, units, nav)

        st.markdown('---')
            
        # Display entries with checkboxes in the sidebar
        st.markdown("<h1 style='text-align: center;'>Schemes Entries</h1>", unsafe_allow_html=True)
        
         # check which checkboxes are checked
        st.session_state.portfolio = check_ckbox()

        # print("Portfolio shape",portfolio.shape)
        if st.session_state.portfolio.shape[0] >0:
                    # get consolidated holdings
                    all_scheme_names = st.session_state.portfolio['Scheme Name'].to_list()
                    all_units = st.session_state.portfolio['Units'].to_list()
                    all_nav = st.session_state.portfolio['NAV'].to_list()
                        
                    with Pool() as pool:
                        results = pool.starmap(get_holdings, [(st.session_state.portfolio, scheme_name, units, nav) for scheme_name, units, nav in zip(all_scheme_names, all_units, all_nav)])
                    

                    consol_holdings = pd.concat(results, ignore_index=True)
                    st.session_state["consol_holdings"] = consol_holdings


    # Render the navigation bar
    navigation = st_navbar(pages, styles=styles_nav,selected='About')



    
    if navigation == 'About':
        nav_about()
    elif navigation == 'Scheme Distribution':
        nav_scheme_distribution(st.session_state.portfolio)
    elif navigation == 'Scheme Compare':
        nav_scheme_compare(st.session_state.portfolio)
    elif navigation == 'Portfolio Analysis':
        nav_portfolio(st.session_state.portfolio)

        
        

          

# Call the main function
if __name__ == "__main__":
    main()
