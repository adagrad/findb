import os

import pandas as pd


def get_new_indices(df: pd.DataFrame, **filenames_index_col):

    for file, index_col in filenames_index_col.items():
        new_elements = []

        if os.path.exists(file):
            # pandas.Index.difference
            # Return a new Index with elements of index not in other.
            try:
                new = df.index.difference(pd.read_csv(file, index_col=index_col).index)
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
