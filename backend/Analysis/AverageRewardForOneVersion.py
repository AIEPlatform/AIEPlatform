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
import json

def AverageRewardForOneVersion(df, selectedVersion, selectedVariable, selectedPolicy, per_day="D"):
    # Filter dataframe
    filtered_df = df[(df['treatment'] == selectedVersion) &  
                     (df['assigner'] == selectedPolicy)]
    # Select columns
    filtered_df = filtered_df[['treatment', 'assigner', 'outcome', 'outcome.timestamp', selectedVariable]]

    # Format rewardTimestamp
    filtered_df['outcome.timestamp'] = pd.to_datetime(filtered_df['outcome.timestamp'])
    filtered_df.dropna(subset=['outcome.timestamp'], inplace=True)
    filtered_df['outcome.timestamp'] = filtered_df['outcome.timestamp'].dt.to_period(per_day)
    
    # Group by rewardTimestamp and calculate mean and standard error of outcome
    result_df = round(filtered_df.groupby('outcome.timestamp').agg({
        'outcome': ['mean', 'std', 'count', lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)]
    }),3)
    # reset index
    result_df.reset_index(inplace=True)
    
    # Rename columns
    result_df.columns = ['time','mean', 'std', 'count', '25th quantile', '75th quantile']
    result_df['time'] = result_df['time'].astype(str)
    return json.loads(result_df.to_json(orient="records")), [c for c in result_df.columns if c != 'time']