import os
import re
from typing import Dict

import pandas as pd


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
    basefile = re.sub(r'\.\d+$', '', file)

    # check if we have a base file which still has some capacity
    if size_mb is not None and os.path.exists(basefile) and os.path.getsize(basefile) / 1024 / 1024 < size_mb:
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
