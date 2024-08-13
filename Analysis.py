import streamlit as st
import pandas as pd
from streamlit_navigation_bar import st_navbar
from modules.data_processing import  check_ckbox
from modules.data_processing import  nav_scheme_distribution, nav_portfolio, nav_about, nav_scheme_compare
from modules.dashboard import search_fund, add_portfolio_file, get_consol_holdings

from streamlit.components.v1 import html

GA_TRACKING_ID = st.secrets["google_analytics"]["tracking_id"]

html(f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_TRACKING_ID}');
</script>
""")

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
            
            search_fund(search_term)
            

        st.header('OR')

                
        st.header("Upload CSV File")
        st.info("Please upload a CSV file with the following columns: 'Scheme Name', 'Units'")

        # add file uploader
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        # make two columns
        col1, col2 = st.columns(2)

        with col1:
            
            if st.button("Add file", key="add_csv"):            

                with st.spinner("Analyzing..."):
                
                    add_portfolio_file(uploaded_file)
        with col2:

            if st.button("Add sample file", key="add_sample"):            

                with st.spinner("Analyzing..."):
                    
                    uploaded_file = './sample_port.csv'
                    add_portfolio_file(uploaded_file)


        st.markdown('---')
            
        # Display entries with checkboxes in the sidebar
        st.markdown("<h1 style='text-align: center;'>Schemes Entries</h1>", unsafe_allow_html=True)
        
        # check which checkboxes are checked
        st.session_state.portfolio = check_ckbox()

        # check if portfolio is not empty
        if st.session_state.portfolio.shape[0] >0:
                    
                    consol_holdings = get_consol_holdings()

                    # set session state for consol_holdings
                    st.session_state["consol_holdings"] = consol_holdings


    # Render the navigation bar
    navigation = st_navbar(pages, styles=styles_nav,selected='About')



    # Call the appropriate function based on the selected page
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
