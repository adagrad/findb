import os
from datetime import datetime

import pandas as pd

if __name__ == '__main__':
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    out_file = os.path.join(data_path, 'ib_fractional.csv')

    df = pd.read_csv("http://www.ibkr.com/download/fracshare_stk.csv")
    df = df.rename(columns={"#SYMBOL": "SYMBOL"}).set_index(["SYMBOL", "MAIN_EXCHANGE"])
    df["last_update"] = datetime.now()
    df.to_csv(out_file)
