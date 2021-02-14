import logging
import os
import sys
import time
from datetime import datetime
import bs4 as bs
import pandas as pd
import requests

from utils.state_utils import load_state, state_exists, remove_state, save_state

_log = logging.getLogger(__name__)

PAGES = [
    "stk",
    "europe_stk",
    "asia_stk",
    "opt",
    "europe_opt",
    "asia_opt",
    "fut",
    "europe_fut",
    "asia_fut",
    "fop",
    "europe_fop",
    "asia_fop",
    "etf",
    "europe_etf",
    "asia_etf",
    "war",
    "europe_war",
    "asia_war",
    "iopt",
    "asia_ipot",
    "ssf",
    "europe_ssf",
    "asia_ssf",
    "fx",
    "cmty",
    "ind",
    "europe_ind",
    "asia_ind",
    "bond",
    "europe_bond",
    "asia_bond",
    "mf",
    "global_mf",
]


def _fetch_ib_markets(page: str):
    url = f'https://www.interactivebrokers.com/en/index.php?f=1563&p={page}'
    try:
        resp = requests.get(url)
        html = bs.BeautifulSoup(resp.text, features="lxml")
        parsed_table = html.find_all(name='table')[0]

        data = [([None] if len(row.find_all('td')) < 4 else []) + [('https://www.interactivebrokers.com/en/' + td.a['href']) if td.find('a') else ''.join(td.stripped_strings)
                for td in row.find_all('td')]
                 for row in parsed_table.find_all('tr')]

        df = pd.DataFrame(data[1:], columns=["country_region", "market_center_details", "products", "hours"])
        return df.fillna(method='ffill')
    except Exception as e:
        print(url, e)
        return pd.DataFrame({})


class IBSymbols(object):

    def __init__(self, pages, statefile):
        self.pages = list(zip(*[pages[c].to_list() for c in pages.columns]))
        self.num_pages = len(self.pages)
        self.statefile = statefile
        self.page_num = 1
        self.frames = []
        self.csv_args = {}

    def download(self, start_time, max_seconds, csv_file=None):
        print(f"continue with {len(self.frames)} frames")
        tst = pd.Timestamp.now()
        i = 0

        while len(self.pages) > 0:
            page, product = self.pages[0]
            exchange = [arg.replace("exch=", "") for arg in page.split("&") if arg.startswith("exch=")]

            for df in self._fetch_ib_symbols(page):
                df['exchange'] = exchange[0] if len(exchange) > 0 else None
                df['product'] = product
                df['last_update'] = tst
                i += 1

                if csv_file is None:
                    self.frames.append(df)
                else:
                    df.to_csv(csv_file, index=False, **self.csv_args)
                    self.csv_args = dict(mode='a', header=False)

                if (start_time - datetime.now()).seconds > max_seconds:
                    save_state(self, self.statefile)
                    raise TimeoutError("too much time elapsed!")

                if i % 10 == 0:
                    save_state(self, self.statefile)

            # get rid of page
            self.page_num = 1
            self.pages.pop(0)
            print(len(self.pages), "left of", self.num_pages)

    def get_result(self):
        return pd.concat(self.frames, axis=0)

    def _fetch_ib_symbols(self, page: str, sleep=None):
        try:
            lenf = 1
            last_symbols = None

            while lenf > 0:
                print(f"load: {page}&page={self.page_num}")
                dfs = pd.read_html(f"{page}&page={self.page_num}")
                had_symbols = False

                for df in dfs:
                    if "IB Symbol" in df.columns:
                        lenf = -1 if df["IB Symbol"].to_list() == last_symbols else len(df)
                        yield df
                        had_symbols = True
                        last_symbols = df["IB Symbol"].to_list()

                if not had_symbols:
                    print(f"no symbols found for page {page}&page={self.page_num}!")
                    lenf = 0

                self.page_num += 1
                if sleep is not None:
                    time.sleep(sleep)

        except Exception as e:
            print(f"failed for: {page}")
            _log.error(e)
            yield pd.DataFrame({})


if __name__ == '__main__':
    max_minutes = int(sys.argv[-1]) if len(sys.argv) > 1 and not sys.argv[-1].startswith("-") else 99999999999
    skip_markets = "--skip-markets" in sys.argv
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    state = os.path.join(data_path, '.state', 'ib_symbols.pickle')
    markets_file = os.path.join(data_path, "ib_markets.csv")
    symbol_file = os.path.join(data_path, "ib_symbols.csv")

    if skip_markets:
        df = pd.read_csv(markets_file)
    else:
        df = pd.concat([_fetch_ib_markets(page) for page in PAGES], axis=0)
        df.to_csv(markets_file)

    symbol_fetcher = load_state(state) if state_exists(state) else IBSymbols(df[["market_center_details", "products"]], state)

    try:
        symbol_fetcher.download(datetime.now(), 60 * max_minutes, symbol_file)
        remove_state(state)
    except TimeoutError as te:
        print(te)
