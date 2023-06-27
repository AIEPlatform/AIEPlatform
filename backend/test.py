
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