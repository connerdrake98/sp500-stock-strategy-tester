import requests
from bs4 import BeautifulSoup
import pandas as pd

URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
r = requests.get(URL)

soup = BeautifulSoup(r.content, 'html5lib')
table_body = soup.find('table', attrs = {'wikitable sortable'}).find('tbody')

tickers = []
names = []
GICS_sectors = []
GICS_sub_industries = []
headquarters_locations = []
dates_added = []
central_index_keys = []
years_founded = []

sp500_info = [
    tickers,
    names,
    GICS_sectors,
    GICS_sub_industries,
    headquarters_locations,
    dates_added,
    central_index_keys,
    years_founded
]

for row in table_body.findAll('tr'):
    i = 0
    for cell in row.findAll('td'):
        sp500_info[i].append(cell.text.strip())
        i = i + 1

sp500_info_dict = dict(zip([
    'tickers',
    'names',
    'GICS_sectors',
    'GICS_sub_industries',
    'headquarters_locations',
    'dates_added',
    'central_index_keys',
    'years_founded'
], sp500_info))

sp500_info_df = pd.DataFrame(sp500_info_dict)

sp500_info_df.to_csv('sp500-info.csv', index=False)