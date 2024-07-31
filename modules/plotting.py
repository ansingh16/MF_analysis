import altair as alt
import streamlit as st
from thefuzz import process



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

    # Calculate current value in schemes
    all_scheme_value = consol_df['Units'] * consol_df['NAV']
    # get total value
    total_value = all_scheme_value.sum()
    consol_df['Fraction Value'] = (all_scheme_value / total_value)*100


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




def portfolio_plots(consol_df):

    # drop null values in weighting
    consol_holdings = consol_df.dropna(subset=['Percent Contribution'])
        
    # fill None in sector column with holdingType
    consol_holdings['Sector'] =consol_holdings['Sector'].fillna(consol_holdings['holdingType'])



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

                    st.write(f'In the following Funds:')

                    comdat = top_companies[top_companies["Company"] == matched_name]

                    for scheme,per_con, per_val in zip(comdat['Scheme Name'],comdat['Percent Contribution'],comdat['Percentage by Value']):

                        st.write(f'{scheme} | Percent Contribution={per_con:.2f}% | Percentage by Value {per_val:.2f}%')
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

