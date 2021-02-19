import math
import os
import sys
import traceback
from datetime import datetime
from time import sleep
from typing import Set
from urllib.parse import quote

import pandas as pd
import requests

from utils.state_utils import load_state, save_state, state_exists


class TickerFinder(object):
    # inspired by: https://github.com/Benny-/Yahoo-ticker-symbol-downloader

    user_agent = 'yahoo-ticker-symbol-downloader'
    general_search_characters = 'abcdefghijklmnopqrstuvwxyz0123456789.='
    first_search_characters = 'abcdefghijklmnopqrstuvwxyz'
    headers = {'User-agent': user_agent}
    query_string = {'device': 'console', 'returnMeta': 'true'}
    illegal_tokens = ['null']
    max_retries = 4

    def __init__(self, existing_symbols: Set[str]):
        self.rsession = requests.Session()
        self.existing_symbols = existing_symbols
        self.queries = []

    def fetch(self):
        self._add_queries()

        while len(self.queries) > 0:
            query = self.queries[0]
            df = self._next_request(query)
            yield df

            # now get rid of query
            self.queries.pop(0)

    def _add_queries(self, prefix=''):
        if len(prefix) == 0:
            search_characters = TickerFinder.first_search_characters
        else:
            search_characters = TickerFinder.general_search_characters

        for i in range(len(search_characters)):
            element = str(prefix) + str(search_characters[i])
            # TODO here we could be more clever with the condition: and element not in self.queries:
            #  lets say we not only have the query in the known symbols but we also know that the symbol as more then 10
            #  matches, we already can dig one level deeper. most likely the same way as we do in the generator
            #          if (count >= 10):
            #             self._add_queries(query_str)
            #  watch out for the recursion depth
            if element not in TickerFinder.illegal_tokens and element not in self.queries and element not in self.existing_symbols:
                self.queries.append(element)

    def _nr_of_hits(self, query_str):
        return len([s for s in self.existing_symbols if query_str in s])

    def _fetch(self, query_str):
        def _encodeParams(params):
            encoded = ''
            for key, value in params.items():
                encoded += ';' + quote(key) + '=' + quote(str(value))
            return encoded

        params = {
            'searchTerm': query_str,
        }

        protocol = 'https'
        req = requests.Request('GET',
                               protocol +'://finance.yahoo.com/_finance_doubledown/api/resource/searchassist' + _encodeParams(params),
                               headers=TickerFinder.headers,
                               params=TickerFinder.query_string
                               )

        req = req.prepare()
        print("req " + req.url)
        resp = self.rsession.send(req, timeout=(12, 12))
        resp.raise_for_status()

        return resp.json()

    def _next_request(self, query_str):
        def decode_symbols_container(json):
            df = pd.DataFrame(json['data']['items'])

            count = len(df)
            if count > 0:
                df = df[~df["symbol"].isin(self.existing_symbols)]
                self.existing_symbols.update(df["symbol"].to_list())

            return df, count

        success = False
        retry_count = 0
        json = None

        # Eponential back-off algorithm
        # to attempt 5 more times sleeping 5, 25, 125, 625, 3125 seconds
        # respectively.
        while(success == False):
            try:
                json = self._fetch(query_str)
                success = True
            except (requests.HTTPError,
                    requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectionError) as ex:
                if retry_count < TickerFinder.max_retries:
                    attempt = retry_count + 1
                    sleep_amt = int(math.pow(5, attempt))
                    print(f"Retry attempt: {attempt} of {TickerFinder.max_retries}. Sleep period: {sleep_amt} seconds.")
                    sleep(sleep_amt)
                    retry_count = attempt
                else:
                    raise

        (symbols, count) = decode_symbols_container(json)

        if (count >= 10):
            self._add_queries(query_str)

        return symbols




if __name__ == '__main__':
    #max_loops = int(sys.argv[1]) if len(sys.argv) > 1 else None
    max_minutes = int(sys.argv[1]) if len(sys.argv) > 1 else None

    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    state = os.path.join(data_path, '.state', 'fetch_yahoo_tickers.pickle')
    file = os.path.join(data_path, 'yahoo_symbols.csv')

    current_symbols = set(pd.read_csv(file)['symbol'].to_list()) if os.path.exists(file) else {}
    resume = state_exists(state)

    tf = load_state(state) if resume else TickerFinder(current_symbols)
    started = datetime.now()
    print(f"started at: {started}")

    try:
        for i, df in enumerate(tf.fetch()):
            if len(df) > 0:
                df = df[['symbol', 'name', 'exch', 'exchDisp', 'type', 'typeDisp']]
                df.to_csv(file, index=False, **(dict(mode='a', header=False) if resume else {}))

                if i % 10 == 0:
                    print(f"fetched {i} dataframes")

                if max_minutes is not None and (datetime.now() - started).seconds / 60 > max_minutes:
                    raise ValueError(f"maximum allowed {max_minutes} minutes reached")

        # we have reached the very end of the loop
        # next time we will restart from the beginning and therefore get rid of the state
        if os.path.exists(state):
            try:
                print("remove state")
                os.remove(state)
            except Exception as e:
                print(e)

            print(f"finished at: {datetime.now()} // {datetime.now() - started}")
    except Exception as e:
        save_state(tf, state)
        traceback.print_exc()
        print(f"paused at: {datetime.now()} // {datetime.now() - started}")
