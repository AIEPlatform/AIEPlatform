import pandas as pd
import numpy as np
# from helpers import get_dataset


def get_stats(group):
    stats = {}
    stats['Mean reward'] = group['reward'].mean()
    stats['Count'] = group['reward'].count()
    stats['unique_id'] = group['learner_id'].nunique()
    # stats['Count of non-response'] = group['reward'].isnull().sum()
    # stats['% of non-response'] = round(group['reward'].isnull().mean() * 100,2)
    
    return pd.Series(stats, index=['Count','Mean reward','unique_id'])


def default_table(data, contextual_name):
    output_table = None
    if contextual_name == "no contextual":
        output_table = data.groupby(['arm']).apply(get_stats)
    else:
        output_table = data.groupby(['arm', contextual_name]).apply(get_stats)
    # Output table description:
    # ...
    return output_table.reset_index()


# def test():
#     df = get_dataset("1233")
#     print(default_table(df, "CONTEXTUAL_weekdayorweekend"))

# test()