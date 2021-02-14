import json
import os
import re
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from string import Template
import pandas as pd
from yfinance.utils import get_json

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
            if i > 0 and i % 10 == 0:
                print(url)
                df = pd.DataFrame(info)
                df.set_index("symbol").to_csv(self.datafile, **self.csv_args)
                self.csv_args = dict(mode='a', header=False)
                save_state(self, self.statefile)
                info = YfDetail._new_dict()

            if (datetime.now() - start_time).seconds / 60 > max_minutes:
                raise TimeoutError(f"{max_minutes} reached")

            self.symbols.pop(0)


if __name__ == '__main__':
    symbol_file = sys.argv[1]
    delta = sys.argv[2] == 'True' if len(sys.argv) > 2 else False
    max_minutes = int(sys.argv[-1]) if len(sys.argv) > 1 and re.match(r"\d+", sys.argv[-1]) else 9999999

    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    state = os.path.join(data_path, '.state', 'fetch_yahoo_info.pickle')
    out = os.path.join(data_path, 'yahoo_info.csv')

    if state_exists(state):
        yf_detail = load_state(state)
    else:
        symbols = pd.read_csv(symbol_file)

        if delta and os.path.exists(out):
            info_symbols = set(pd.read_csv(out)["symbol"].to_list())
            symbols = symbols[~symbols['symbol'].isin(info_symbols)]

        yf_detail = YfDetail(state, out, symbols['symbol'].to_list())
    try:
        yf_detail.fetch(max_minutes)
    except Exception as e:
        traceback.print_exc()
        sys.exit()

    # we have got all information possible
    remove_state(state)
