import argparse
import os
import sys
import traceback
from datetime import datetime

import pandas as pd
from yfinance.utils import get_json

from utils.df_utils import load_csv, get_next_partition_file
from utils.state_utils import save_state, load_state, state_exists, remove_state


class YfDetail(object):
    
    @staticmethod
    def _new_dict():
        headers = "symbol exchange shortName exchangeTimezoneName exchangeTimezoneShortName isEsgPopulated gmtOffSetMilliseconds messageBoardId market longName" \
                  "companyOfficers twitter name startDate description maxAge zip sector fullTimeEmployees longBusinessSummary city phone state country website address1 address2 address3 industry" \
                  "initInvestment family categoryName initAipInvestment subseqIraInvestment brokerages managementInfo subseqInvestment legalType styleBoxUrl feesExpensesInvestment feesExpensesInvestmentCat initIraInvestment subseqAipInvestment"

        return {k: [] for k in headers.split(" ")}

    def __init__(self, statefile: str, datafile: str, symbols: list):
        self.symbols = symbols
        self.statefile = statefile
        self.datafile = datafile
        self.csv_args = {}

    def fetch(self, max_minutes=99999999):
        print(f"start fetching info for {len(self.symbols)} symbols")
        start_time = datetime.now()
        info = YfDetail._new_dict()
        i = 0

        def dict_walker(d: dict, key):
            if key in d:
                return d[key]

            for k, v in d.items():
                if isinstance(v, dict):
                    res = dict_walker(v, key)
                    if res is not None:
                        return res

            return None

        while len(self.symbols) > 0:
            symbol = self.symbols[0]
            url = f"https://finance.yahoo.com/quote/{symbol}"

            try:
                data = get_json(url)
                data["symbol"] = symbol
                for k, v in info.items():
                    v.append(dict_walker(data, k))

            except Exception as e:
                print(f"Not able to find the data for {url}", e)

            i += 1
            if i > 0 and (i % 10 == 0 or len(self.symbols) <= 1):
                print(url)
                df = pd.DataFrame(info)

                # we eventually need to start a new partition file after we reached 50MB
                self.datafile = get_next_partition_file(self.datafile, 50)
                if not os.path.exists(self.datafile): self.csv_args = {}
                df.set_index("symbol").to_csv(self.datafile, **self.csv_args)

                # make sure we only append data from here on
                self.csv_args = dict(mode='a', header=False)
                save_state(self, self.statefile)
                info = YfDetail._new_dict()

            if (datetime.now() - start_time).seconds / 60 > max_minutes:
                raise TimeoutError(f"{max_minutes} reached")

            self.symbols.pop(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--symbol-file', type=str)
    parser.add_argument('-d', '--delta', action="store_true")
    parser.add_argument('-t', '--max-time', type=int, default=9999999)

    args = parser.parse_args()

    symbol_file = args.symbol_file
    delta = args.delta
    max_minutes = args.max_time

    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    state = os.path.join(data_path, '.state', 'fetch_yahoo_info.pickle')
    out = os.path.join(data_path, 'yahoo_info.csv')

    print(f"use {symbol_file} with delta: {delta}, running maximum {max_minutes} minutes")
    dfs = pd.read_csv(symbol_file, index_col='symbol')

    # make sure we have a unique set of symbols but as type list
    if delta:
        symbols = dfs.index.difference(load_csv(out, index_col='symbol').index)
    else:
        symbols = dfs.index

    dfs = None
    yf_detail = YfDetail(state, out, list(set(symbols.to_list())))

    try:
        yf_detail.fetch(max_minutes)
    except Exception as e:
        traceback.print_exc()
        sys.exit()

    # we have got all information possible
    remove_state(state)
