import mstarpy
import pandas as pd
import datetime
import streamlit as st
from modules.data_processing import add_portfolio_entry, process_fund, get_holdings
from multiprocessing import Pool


def search_fund(search_term):

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

        return

def add_portfolio_file(uploaded_file):
      
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


            return


@st.cache_data
def get_consol_holdings():

    # get consolidated holdings
    all_scheme_names = st.session_state.portfolio['Scheme Name'].to_list()
    all_units = st.session_state.portfolio['Units'].to_list()
    all_nav = st.session_state.portfolio['NAV'].to_list()
                        
    with Pool() as pool:
        results = pool.starmap(get_holdings, [(st.session_state.portfolio, scheme_name, units, nav) for scheme_name, units, nav in zip(all_scheme_names, all_units, all_nav)])
                    

    consol_holdings = pd.concat(results, ignore_index=True)

    return consol_holdings
                    
