import logging
import os

import bs4 as bs
import pandas as pd
import requests
from cachier import cachier

from utils.time_utils import time_until_end_of_day

_log = logging.getLogger(__name__)


def download_optionable_stocks(pages=None):
    # fetch optionable stocks
    if pages is None:
        pages = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z IND ETF".split(" ")

    df = pd.concat([_fetch_optionable_symbols(page) for page in pages], axis=0)

    # extract symbol
    symbol = df['CompanyName'].str.extract(r'^\(([^\(\)]+)\)').iloc[:, 0].rename("Symbol")
    symbol = symbol.str.replace("$", "^")

    if len(symbol[symbol.isnull().values]) > 0:
        raise ValueError(f"Could not extract Symbol:\n{df[symbol.isnull().values]}")

    # remove symbol from company name
    df['CompanyName'] = df["CompanyName"].str.replace(r'\([^\)]+\)', '')

    # make symbol the index and add drop unnecessary data
    df.index = symbol
    df = df.sort_index()
    df = df.drop_duplicates(keep='last').sort_index()
    df['Last Update'] = pd.Timestamp.now()
    return df


@cachier(stale_after=time_until_end_of_day())
def _fetch_optionable_symbols(page: str):
    try:
        resp = requests.get(f'https://www.poweropt.com/optionable.asp?fl={page}')
        html = bs.BeautifulSoup(resp.text, features="lxml")
        parsed_table = html.find_all(attrs={'id': 'example'})[0]

        data = [[('https://www.poweropt.com/' + td.a['href']) if td.find('a') else ''.join(td.stripped_strings)
                 for td in row.find_all('td')]
                for row in parsed_table.find_all('tr')]

        df = pd.DataFrame(data[1:], columns=data[0])
        df["Type"] = "STOCK" if len(page) <= 1 else page
        return df
    except Exception as e:
        _log.error(e)
        return pd.DataFrame({})


if __name__ == '__main__':
    df = download_optionable_stocks()
    file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "optionable.csv")
    df.to_csv(file)
