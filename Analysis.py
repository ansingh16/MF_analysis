import streamlit as st
import pandas as pd
import altair as alt
from streamlit_navigation_bar import st_navbar
import mstarpy
import datetime
from multiprocessing import Pool
from mstarpy import search_funds

from modules.data_processing import process_fund, add_portfolio_entry
from modules.data_processing import  check_ckbox
from modules.data_processing import  get_holdings
from modules.data_processing import  nav_scheme_distribution, nav_portfolio, nav_about, nav_scheme_compare



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
if 'top_companies' not in st.session_state:
    st.session_state.top_companies = None


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



def main():
    
    
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
