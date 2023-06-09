import pandas as pd
import numpy as np

import sys

from credentials import *

import itertools

def get_all_combinations(array):
    all_combinations = []
    for r in range(1, len(array) + 1):
        combinations = itertools.combinations(array, r)
        all_combinations.extend(combinations)
    return all_combinations


def get_stats(df, group_by):
    # stats = {}
    # stats['Mean outcome'] = group['outcome'].mean()
    # stats['Count'] = group['outcome'].count()
    # # stats['Count of non-response'] = group['reward'].isnull().sum()
    # # stats['% of non-response'] = round(group['reward'].isnull().mean() * 100,2)

    df = df.groupby(group_by) \
       .agg(count=('outcome', 'size'), mean=('outcome', 'mean')) \
       .reset_index()

    return df


def basic_reward_summary_table(df, selectedVariables):
    result_df = None
    data = df
    if len(selectedVariables) == 0:
        result_df = get_stats(data, ['treatment'])
    else:
        all_combs = get_all_combinations(selectedVariables)
        group_bys = [['treatment']] + [['treatment'] + list(comb) for comb in all_combs]
        grouped_dfs = []
        for group in group_bys:

            grouped = get_stats(data, group)
            grouped_dfs.append(grouped)

        result_df = pd.concat(grouped_dfs, axis=0, ignore_index=True)
    desired_columns = [col for col in result_df.columns if col not in ['count', 'mean']] + ['count', 'mean']

    # Reorder the columns
    result_df = result_df[desired_columns]
    return result_df