from credentials import *
from Analysis.AverageRewardByTime import AverageRewardByTime
def test():
    df = getDataset("64887e32882568e41f7205bd")
    print(AverageRewardByTime(df, ['gender']))

test()