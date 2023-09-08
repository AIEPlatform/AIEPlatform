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
AssignerIndividualLevelInformation.delete_many({})


def two_var_strong_predictor(num_users = 100):
    for user in range(1, num_users + 1):
        users.append(f'sim_user_{user}')
        name = f'sim_user_{user}'
        users_status[name] = "no_arm"
    def one_user(user, i):

        # at this point, we know their gender.
        predictor = None
        for variable in variables:
            # randomly get 0 or 1
            predictor = random.randint(0, 1)
            give_variable_value(deployment, study, variable, user, predictor)

        k = 0
        while k < 10:
            k+=1
            time.sleep(1) # every 2 seconds I pick a random user, assign arm or send reward.
            number = random.random()
            if False: 
                pass
            else:
                # get arm
                version_to_show = assign_treatment(deployment, study, user)['name']


                # give reward
                arm_indicator = 1 if version_to_show == "version1" else 0
                reward_prob = 0.4 + predictor * arm_indicator * 0.3 - arm_indicator * 0.2
                value = 1 if random.random() < reward_prob else 0
                if random.random() < reward_prob:
                    get_reward(deployment, study, user, value)
                else:
                    get_reward(deployment, study, user, value)
            print(f"*** predictor {str(predictor)} is gives reward {str(value)} on arm {version_to_show}")

    for i in range(0, len(users)):
        user = users[i]
        t = threading.Thread(target=one_user, args=(user, i))
        t.start()

num_users = 300
deployment = 'Sim'
study = 'ts_uniform'
variables = ['gender']
two_var_strong_predictor(num_users = num_users)