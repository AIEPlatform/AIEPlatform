from credentials import *
from Analysis.AverageRewardByTime import AverageRewardByTime
import datetime
from Models.VariableValueModel import VariableValueModel
def test():
    # the_interactions = list(Interaction.find({"moocletId": ObjectId("648877fbb11c95ea10e140cd")}))
    # # change the rewardTimestamp this way:
    # # first 20% of the interactions, change the rewardTimestamp to four days ago.
    # # second 20% of the interactions, change the rewardTimestamp to three days ago.
    # # third 20% of the interactions, change the rewardTimestamp to two days ago.
    # # fourth 20% of the interactions, change the rewardTimestamp to one day ago.
    # # fifth 20% of the interactions, change the rewardTimestamp: no change.
    
    # for i in range(0, len(the_interactions)):
    #     time = datetime.datetime.now()
    #     if i < 0.1 * len(list(the_interactions)):
    #         time = datetime.datetime.now() - datetime.timedelta(days=9)
    #     if i < 0.2 * len(list(the_interactions)):
    #         time = datetime.datetime.now() - datetime.timedelta(days=8)
    #     elif i < 0.3 * len(list(the_interactions)):
    #         time= datetime.datetime.now() - datetime.timedelta(days=7)
    #     elif i < 0.4 * len(list(the_interactions)):
    #         time = datetime.datetime.now() - datetime.timedelta(days=6)
    #     elif i < 0.5 * len(list(the_interactions)):
    #         time = datetime.datetime.now() - datetime.timedelta(days=5)
    #     elif i < 0.6 * len(list(the_interactions)):
    #         time = datetime.datetime.now() - datetime.timedelta(days=4)
    #     elif i < 0.7 * len(list(the_interactions)):
    #         time= datetime.datetime.now() - datetime.timedelta(days=3)
    #     elif i < 0.8 * len(list(the_interactions)):
    #         time = datetime.datetime.now() - datetime.timedelta(days=2)
    #     elif i < 0.9 * len(list(the_interactions)):
    #         time = datetime.datetime.now() - datetime.timedelta(days=1)
    #     else:
    #         time = datetime.datetime.now()

    #     Interaction.update_one({"_id": the_interactions[i]['_id']}, {"$set": {"rewardTimestamp": time}})
    #     # interaction.save()
    print(VariableValueModel.getLatestVariableValues(['wantToTravel'], 'sim_user_1'))

test()