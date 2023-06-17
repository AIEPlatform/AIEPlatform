# Function description
# First, need to filter df by selectedVersion, selectedVariable, selectedPolicy.
# Secondly, format the rewardTimestamp to a certain format by per ("day", "week", "month", "year"). (this can be done later)
# group by the formatted rewardTimestamp, calculate the mean of the outcome, stderros, 25, 75 cis... (you can choose how we interpret the error bars)
# Return is a dataframe that's like:
# time, mean, errorBarEnd1, errorBarEnd2

# Function description
# First, need to filter df by selectedVersion, selectedVariable, selectedPolicy.
# Secondly, format the rewardTimestamp to a certain format by per ("day", "week", "month", "year"). (this can be done later)
# group by the formatted rewardTimestamp, calculate the mean of the outcome, stderros, 25, 75 cis... (you can choose how we interpret the error bars)
# Return is a dataframe that's like:
# time, mean, errorBarEnd1, errorBarEnd2
# ! per_day need to be defined as day - 'd', Month - 'm', Year - 'y', Week - 'w'
import pandas as pd
import numpy as np
import sys
from credentials import *
import itertools
from scipy import stats


def average_reward_for_one_version(df, selectedVersion, selectedVariable, selectedPolicy, per_day="d"):
    # Filter dataframe``
    filtered_df = df[(df['treatment'] == selectedVersion) &  
                     (df['policy'] == selectedPolicy)]
    # Select columns
    filtered_df = filtered_df[['treatment', 'policy', 'outcome', 'outcome.timestamp', selectedVariable]]

    # Format rewardTimestamp
    filtered_df['outcome.timestamp'] = pd.to_datetime(filtered_df['outcome.timestamp'])
    filtered_df['outcome.timestamp'] = filtered_df['outcome.timestamp'].dt.to_period(per_day)
    
    # Group by rewardTimestamp and calculate mean and standard error of outcome
    result_df = filtered_df.groupby('outcome.timestamp').agg({
        'outcome': ['mean', 'std', 'count', lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)]
    })
    # reset index
    result_df.reset_index(inplace=True)
    
    # Rename columns
    result_df.columns = ['time','mean', 'std', 'count', 'errorBarEnd1', 'errorBarEnd2']

    return result_df