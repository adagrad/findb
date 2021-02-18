import argparse
import os
import sqlite3
import sys
import traceback
from datetime import datetime

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine


def mysql_replace_into(table, conn, keys, data_iter):
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.sql.expression import Insert

    @compiles(Insert)
    def replace_string(insert, compiler, **kw):
        s = compiler.visit_insert(insert, **kw)
        s = s.replace("INSERT INTO", "REPLACE INTO")
        return s

    data = [dict(zip(keys, row)) for row in data_iter]

    conn.execute(table.table.insert(replace_string=""), data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source-db', type=str)
    parser.add_argument('-d', '--destination-db', type=str)
    parser.add_argument('-b', '--begin', type=str, default=None)
    parser.add_argument('-e', '--end', type=str, default=None)
    parser.add_argument('-x', '--exchange', type=str, default='-1', help="only fetch prices for a single exchange")
    parser.add_argument('-u', '--update-missing', action='store_true', help="only fetch if no price exists for the given date range")
    parser.add_argument('-a', '--append', action='store_true', help="append new symbols and dates (target db need to exist)")
    parser.add_argument('-t', '--max-time', type=int, help="maximum runtim time in minutes", default=60 * 5)
    args = parser.parse_args()

    db1 = os.path.abspath(args.source_db)
    db2 = os.path.abspath(args.destination_db)
    exchange = args.exchange
    min_date = args.begin
    max_date = args.end
    max_time = args.max_time
    period = "max" if min_date is None and max_date is None else None
    only_new_symbols = args.update_missing
    append_existing_data = args.append

    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    state = os.path.join(data_path, '.state', 'fetch_yahoo_prices.pickle')
    start_time = datetime.now()
    max_exceptions = 10
    exceptions = 0

    con = sqlite3.connect(db1)
    cur = con.cursor()

    cur.execute("ATTACH DATABASE ? AS price", (db2,))

    if append_existing_data or only_new_symbols:
        sql = "select ys.symbol, ys.exchange, coalesce(max(yp.date), date('1950-01-01')) as maxdate \n" \
              "from yf_symbol ys"

        if only_new_symbols:
            sql += "\njoin price.yf_price yp on yp.symbol = ys.symbol"
        else:
            sql += "\nleft outer join price.yf_price yp on yp.symbol = ys.symbol"
    else:
        sql = "select ys.symbol, ys.exchange, date('1950-01-01') as maxdate \n" \
              "from yf_symbol ys" \

    sql += "\nwhere 1 = 1 "

    if exchange is not None:
        sql += f"\n   and ys.exchange = '{exchange}'"
    if only_new_symbols:
        subquery = "select distinct symbol from price.yf_price where 1 = 1"
        if min_date is not None: subquery += f" and date >= '{min_date}'"
        if max_date is not None: subquery += f" and date <= '{max_date}'"
        sql += f"\n    and ys.symbol not in ({subquery})"

    if append_existing_data or only_new_symbols:
        sql += "\ngroup by ys.symbol, ys.exchange"

    print(f"import into {db2} from {min_date} to {max_date}")
    print(sql)

    # continue from state or start from query
    symbols = list(cur.execute(sql))
    try:
        cur.execute("DETACH DATABASE price")
    except Exception:
        pass

    engine = create_engine(f'sqlite:///{db2}')
    print(f"processing {len(symbols)} symbols")

    # start loading the quotes database
    with engine.connect() as con:
        while len(symbols) > 0:
            symbol, exchange, last_available_date = symbols[0]
            min_date = min(str(last_available_date)[:10], min_date)
            print(symbol, exchange, min_date)

            try:
                df = yf.Ticker(symbol).history(interval='1d', period=period, start=min_date, end=max_date, prepost=True, auto_adjust=False, back_adjust=False)
                df = df.rename(columns={"Adj Close": "adj_close", "Stock Splits": "stock_splits"})
                df.index = pd.MultiIndex.from_product([[symbol], df.index], names=("symbol", "date"))

                df.to_sql('yf_price', engine, if_exists='append', method=mysql_replace_into)
                exceptions = 0
            except Exception as e:
                exceptions += 1
                if exceptions >= max_exceptions:
                    print("maximum exceptions in a row reached! ")
                    traceback.print_exc()
                    sys.exit(os.EX_IOERR)

            if (datetime.now() - start_time).seconds / 60 > max_time:
                print("maximum time reached!")
                sys.exit(os.EX_OK)

            symbols.pop(0)

