from pathlib import Path
import streamlit as st
import pandas as pd
import altair as alt
import mstarpy
import datetime
from modules.plotting import portfolio_plots, donut_scheme_holding


def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()



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

    
    # group by company_name and calculate the sum of the value and sort in descending order
    top_companies = consol_df.groupby(['Company', 'Sector','Scheme Name','Percent Contribution'])['Percentage by Value'].sum().reset_index().sort_values(by='Percentage by Value', ascending=False)

   
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
             

            

# Function to process each scheme in parallel
@st.cache_data
def get_holdings(portfolio, scheme_name, units, nav):
    holdings = get_scheme_hold(portfolio, scheme_name)
    holdings['Units'] = float(units)
    holdings['NAV'] = nav
    holdings['Scheme Category'] = portfolio.loc[portfolio["Scheme Name"] == scheme_name, "Scheme Category"].values[0]
    holdings['Scheme Name'] = portfolio.loc[portfolio["Scheme Name"] == scheme_name, "Scheme Name"].values[0]
    return holdings


@st.cache_data
def correlation(df):
    # Aggregate sector allocations by scheme
    sector_allocations = df.groupby(['Scheme Name', 'Sector'])['Percent Contribution'].sum().reset_index()
    
    # Pivot the data to get schemes as rows and sectors as columns
    df_pivot = sector_allocations.pivot(index='Scheme Name', columns='Sector', values='Percent Contribution').fillna(0)
    
    # Compute the correlation matrix between schemes
    correlation_matrix = df_pivot.T.corr()
    
    return correlation_matrix




def nav_scheme_compare(portfolio):
    
    st.markdown("<h2 style='text-align:center'>Scheme Comparison</h2>", unsafe_allow_html=True)

    st.markdown("Please select two schemes from the drop down menu to compare the sectorial allocations and then click on 'Compare' button. This will generate a histogram of the sector allocations of the selected schemes.")

    st.markdown("---")

    if not portfolio.empty:

        if portfolio.shape[0]>=2:
             
            st.markdown("<h3 style='text-align:center'>Scheme Comparison</h3>", unsafe_allow_html=True)


           
            st.markdown("---")


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

        st.markdown("Following is the correlation matrix of the sector allocations of all the schemes in portfolio. To achieve a good portfolio diversification one must make sure that schemes are not highly correlated among themselves in terms of sectorial allocations.")
            

        # Ensure the DataFrame has the necessary columns
        if 'Company' in st.session_state.consol_holdings.columns and 'Sector' in st.session_state.consol_holdings.columns and 'Percent Contribution' in st.session_state.consol_holdings.columns and 'Scheme Name' in st.session_state.consol_holdings.columns:

            consol_holdings = st.session_state.consol_holdings.dropna(subset=['Percent Contribution'])
        
           

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
    
    st.markdown("<h2 style='text-align:center'>Consolidated Portfolio Summary</h2>", unsafe_allow_html=True)

    st.markdown("This tab gives the consolidated portfolio summary. This will tell you the infomation regarding the detail sectorial allocations of the selected portfolio by value and types of the schemes. It shows the sectorial distribution by value of your portfolio. You can search for the allocation for a particular company by entering the company name in the search bar. The table displays the top 10 companies by value for your portfolio followed by top companies or assets in different sectors for yout portfolio.")

    st.markdown("---")



    if not portfolio.empty:

                # get top companies
                st.session_state["top_companies"] = get_top_companies()

                st.markdown("<h2 style='text-align:center'>Consolidated Portfolio Holdings</h2>", unsafe_allow_html=True)
                
               
                # make plots for a portfolio
                portfolio_plots(st.session_state.consol_holdings)
                

                
def nav_about():
    intro_markdown = read_markdown_file("README.md")
    st.markdown(intro_markdown, unsafe_allow_html=True)





def nav_scheme_distribution(portfolio):
    
    st.markdown("<h2 style='text-align:center'>Scheme Distribution</h2>", unsafe_allow_html=True)

    st.markdown("This tab gives the information on the sectorial distribution of a scheme and the holdings of the selected schemes. You can select from the dropdown menu the scheme for which you need the details.")
    st.markdown("---")
    
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

