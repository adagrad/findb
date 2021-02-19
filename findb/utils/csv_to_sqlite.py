import argparse
import csv
import os
import sqlite3


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--files', type=str, nargs='+')
    parser.add_argument('-d', '--db', type=str)
    parser.add_argument('-t', '--table', type=str)
    parser.add_argument('--skip-first-col', action="store_true")
    args = parser.parse_args()

    files = args.files
    db = os.path.abspath(args.db)
    table = args.table
    skip_first_col = args.skip_first_col

    print(f"import {files} into {db} . {table} , skip first col {skip_first_col}")
    con = sqlite3.connect(db)
    cur = con.cursor()

    def insert_batch(batch, row_len):
        params = "(" + ", ".join("?" * row_len) + ")"
        params = ", ".join([params] * (len(batch) // row_len))
        cur.execute("REPLACE INTO " + table + " VALUES " + params, batch)

    for file in files:
        with open(file, 'r') as f:
            # csv.DictReader uses first line in file for column headings by default
            reader = csv.reader(f)
            batch = []
            for i, row in enumerate(reader):
                if i > 0:
                    if skip_first_col:
                        row = row[1:]

                    batch.extend(row)
                    if i % 100 == 0:
                        insert_batch(batch, len(row))
                        batch = []
                else:
                    print(row, " -  skip_first_col:", skip_first_col)

            if len(batch) > 0:
                insert_batch(batch, len(row))

        print(f"imported {i} rows from {file}")

    con.commit()
    con.close()

