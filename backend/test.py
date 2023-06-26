# from credentials import *
# from Analysis.AverageRewardByTime import AverageRewardByTime
# import datetime
# from Models.VariableValueModel import VariableValueModel
# def test():
#     the_interactions = list(Interaction.find({"moocletId": ObjectId("648b1379fd591446c7c1f0b3")}))
#     # change the rewardTimestamp this way:
#     # first 20% of the interactions, change the rewardTimestamp to four days ago.
#     # second 20% of the interactions, change the rewardTimestamp to three days ago.
#     # third 20% of the interactions, change the rewardTimestamp to two days ago.
#     # fourth 20% of the interactions, change the rewardTimestamp to one day ago.
#     # fifth 20% of the interactions, change the rewardTimestamp: no change.
    
#     for i in range(0, len(the_interactions)):
#         time = datetime.datetime.now()
#         if i < 0.1 * len(list(the_interactions)):
#             time = datetime.datetime.now() - datetime.timedelta(days=9)
#         if i < 0.2 * len(list(the_interactions)):
#             time = datetime.datetime.now() - datetime.timedelta(days=8)
#         elif i < 0.3 * len(list(the_interactions)):
#             time= datetime.datetime.now() - datetime.timedelta(days=7)
#         elif i < 0.4 * len(list(the_interactions)):
#             time = datetime.datetime.now() - datetime.timedelta(days=6)
#         elif i < 0.5 * len(list(the_interactions)):
#             time = datetime.datetime.now() - datetime.timedelta(days=5)
#         elif i < 0.6 * len(list(the_interactions)):
#             time = datetime.datetime.now() - datetime.timedelta(days=4)
#         elif i < 0.7 * len(list(the_interactions)):
#             time= datetime.datetime.now() - datetime.timedelta(days=3)
#         elif i < 0.8 * len(list(the_interactions)):
#             time = datetime.datetime.now() - datetime.timedelta(days=2)
#         elif i < 0.9 * len(list(the_interactions)):
#             time = datetime.datetime.now() - datetime.timedelta(days=1)
#         else:
#             time = datetime.datetime.now()

#         Interaction.update_one({"_id": the_interactions[i]['_id']}, {"$set": {"rewardTimestamp": time}})
#         # interaction.save()
#     # print(VariableValueModel.getLatestVariableValues(['wantToTravel'], 'sim_user_1'))

# test()


num_users = 100
import time
import random
from routes.user_interaction import *
users = []
users_status = {}
import threading
from credentials import *
import numpy as np

Interaction.delete_many({})
Lock.delete_many({})
RewardLog.delete_many({})
TreatmentLog.delete_many({})
VariableValue.delete_many({})
MOOCletIndividualLevelInformation.delete_many({})


def two_var_strong_predictor(num_users = 100):
    for user in range(1, num_users + 1):
        users.append(f'sim_user_{user}')
        name = f'sim_user_{user}'
        users_status[name] = "no_arm"
    def one_user(user, i):

        # at this point, we know their gender.

        k = 0
        while k < 100:
            user = str(k)
            predictor = None
            for variable in variables:
                # randomly get 0 or 1
                predictor = random.randint(0, 1)
                give_variable_value(deployment, study, variable, user, predictor)
            #time.sleep(1) # every 2 seconds I pick a random user, assign arm or send reward.
            # get arm
            version_to_show = assign_treatment(deployment, study, user)['name']


            # give reward
            arm_indicator = 1 if version_to_show == "factor=1" else 0
            reward_prob = 0.4 + predictor * arm_indicator * 0.3 - arm_indicator * 0.2
            value = 1 if random.random() < reward_prob else 0
            if random.random() < reward_prob:
                get_reward(deployment, study, user, value)
            else:
                get_reward(deployment, study, user, value)

            k+=1
            #print(f"*** predictor {str(predictor)} is gives reward {str(value)} on arm {version_to_show}")

    for i in range(0, len(users)):
        user = users[i]
        t = threading.Thread(target=one_user, args=(user, i))
        t.start()

num_users = 1
deployment = 'Simulations'
study = 'CHATGPT_VS_TSC'
variables = ['gender']
two_var_strong_predictor(num_users = num_users)


# read interactions_for_posteriors.py

# interaction_ids = []
# with open('interactions_for_posterior.txt', 'r') as f:
#     for line in f:
#         interaction_ids.append(line.strip())

# print(len(interaction_ids))

# # get unique
# interaction_ids = list(set(interaction_ids))
# print(len(interaction_ids))