# Function description
# First, need to filter df by selectedVersion, selectedVariable, selectedPolicy.
# Secondly, format the rewardTimestamp to a certain format by per ("day", "week", "month", "year"). (this can be done later)
# group by the formatted rewardTimestamp, calculate the mean of the outcome, stderros, 25, 75 cis... (you can choose how we interpret the error bars)
# Return is a dataframe that's like:
# time, mean, errorBarEnd1, errorBarEnd2

def average_reward_for_one_version(df, selectedVersion, selectedVariable, selectedPolicy, per_day="day"):
    pass