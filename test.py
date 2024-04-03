import requests
from bs4 import BeautifulSoup
import json
import pandas as pd 
import multiprocessing.pool as Pool

def get_holdings(scheme):
    """
    This function sends a GET request to a specific URL, parses the HTML using BeautifulSoup, 
    finds a script tag with a specific ID, extracts JSON data from the script tag content, and 
    retrieves holdings and creates a pandas DataFrame. No parameters are passed and no return 
    type is specified.
    """
    url = requests.get(data.loc[data['Scheme Name'] == scheme,'scheme_url'].values[0])
    soup = BeautifulSoup(url.text, 'html.parser')

    # Find the script tag with the specific ID
    script_tag = soup.find('script', id='__NEXT_DATA__')

    # Extract the JSON data from the script tag content
    json_data = json.loads(script_tag.contents[0])

    # get holdings
    holdings = json_data['props']['pageProps']['mf']['holdings']

    # get pandas
    hold_df = pd.DataFrame(holdings)

    return hold_df[['company_name','sector_name','corpus_per']]


data = pd.read_csv('sample_port.csv')
all_schemes = data['Scheme Name'].unique()

with Pool.Pool(4) as p:
    consol_df = pd.DataFrame()
    hold_list = p.map(get_holdings, all_schemes)

    for hold_df in hold_list:
        consol_df = pd.concat([hold_df, consol_df], ignore_index=True)

    print(consol_df)
