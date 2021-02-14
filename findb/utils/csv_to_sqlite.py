import csv
import sqlite3
import sys
import os


if __name__ == "__main__":
    file = sys.argv[1]
    db = os.path.abspath(sys.argv[2])
    table = sys.argv[3]
    skip_first_col = len(sys.argv) > 4

    print(f"import into {db}")
    con = sqlite3.connect(db)
    cur = con.cursor()

    def insert_batch(batch, row_len):
        params = "(" + ", ".join("?" * row_len) + ")"
        params = ", ".join([params] * (len(batch) // row_len))
        cur.execute("REPLACE INTO " + table + " VALUES " + params, batch)

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

    print(f"imported {i} rows")
    con.commit()
    con.close()

