import sqlite3
import sys


def merge_db(target_file, *source_files):
    # create con object to connect
    # the database geeks_db.db
    con = sqlite3.connect(target_file)

    # create the cursor object
    cur = con.cursor()

    # execute the script by creating the
    # table named geeks_demo and insert the data
    for src_file in source_files:
        cur.executescript(f"""
            attach '{src_file}' as toMerge;           
            BEGIN; 
            insert into AuditRecords select * from toMerge.AuditRecords; 
            COMMIT; 
            detach toMerge;
        """)


if __name__ == '__main__':
    target = sys.argv[1]
    sources = sys.argv[1:]

    merge_db(target, *sources)
