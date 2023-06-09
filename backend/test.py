from credentials import *
from Analysis.basic_reward_summary_table import basic_reward_summary_table
def test():
    df = getDataset("64834a1a92e5cb2515c525de")
    print(basic_reward_summary_table(df, ['gender']))

test()