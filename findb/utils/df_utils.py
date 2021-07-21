import os
import re
import numpy as np
from typing import Dict, List

import pandas as pd
from bs4 import PageElement, ResultSet


def load_csv(file, *args, **kwargs) -> pd.DataFrame:
    # first read the base file
    frames = [pd.read_csv(file, *args, **kwargs)]

    # then read all eventually existing extra partitions
    for i in range(1, 99):
        part_file = f'{file}{str(i).zfill(2)}'
        if os.path.exists(part_file):
            frames.append(pd.read_csv(part_file, *args, **kwargs))
        else:
            break

    # merge all partitions before we return
    return pd.concat(frames, axis=0)


def get_next_partition_file(file, size_mb=None):
    basefile = re.sub(r'\d+$', '', file)

    if not os.path.exists(basefile):
        return basefile

    # check if we have a base file which still has some capacity
    if size_mb is not None and os.path.getsize(basefile) / 1024 / 1024 < size_mb:
        return basefile

    # next check all extra partitions and return the nex possible file with capacity
    for i in range(1, 99):
        pfile = f'{basefile}{str(i).zfill(2)}'

        if size_mb is not None and os.path.exists(pfile) and os.path.getsize(pfile) / 1024 / 1024 < size_mb:
            return pfile
        elif not os.path.exists(pfile):
            return pfile

    # we should never get here but if this happens (for whatever reason) return the base file
    return basefile


def get_new_indices(df: pd.DataFrame, filenames_index_col: Dict[str, str]) -> pd.Index:
    new_elements = []

    for file, index_col in filenames_index_col.items():
        # get all indices which are in the dataframe but are not in any of the file passed as **kwargs
        if os.path.exists(file):
            try:
                # pandas.Index.difference: Return a new Index with elements of index not in other.
                new = df.index.difference(load_csv(file, index_col=index_col).index)
                new_elements.append(new)
            except IndexError as ie:
                pass

    if len(new_elements) <= 0:
        return df.index
    else:
        idx = new_elements[0]
        for ne in new_elements[1:]:
            idx = idx.union(ne, sort=True)

        return idx


def parse_table_with_links(table: List[PageElement], base_url: str = '') -> pd.DataFrame:
    rows = table.find_all('tr')
    nr_columns = max([sum([2 if col.find('a') else 1 for col in row.find_all('td')]) for row in rows])
    nptable = np.empty((len(rows), nr_columns), dtype=object)
    header = []

    for h in table.find_all('th'):
        for i in range(int(h["colspan"]) if h.has_attr("colspan") else 1):
            header.append(''.join(h.stripped_strings))

    for i, row in enumerate(rows):
        columns = row.find_all('td')
        for j, col in enumerate(columns):
            rowspan = int(col["rowspan"]) if col.has_attr("rowspan") else 1
            colspan = int(col["colspan"]) if col.has_attr("colspan") else 1

            for i2 in range(i, i+rowspan):
                for j2 in range(j, j+colspan):
                    offset = 0
                    while nptable[i2, j2 + offset] is not None:
                        offset += 1

                    if col.find('a'):
                        nptable[i2, j2+offset] = ''.join(col.stripped_strings)
                        nptable[i2, j2+offset+1] = base_url + '/' + col.a['href']
                    else:
                        nptable[i2, j2+offset] = ''.join(col.stripped_strings)

    return pd.DataFrame(nptable) #, columns=header if len(header) > 0 else None)

