num_users = 100
import time
import random
from routes.user_interaction import *
users = []
users_status = {}
import threading
from credentials import *
import numpy as np
import requests
session = requests.Session()
from dotenv import load_dotenv
import json
load_dotenv()

Interaction.delete_many({})
Lock.delete_many({})
RewardLog.delete_many({})
TreatmentLog.delete_many({})
VariableValue.delete_many({})
MOOCletIndividualLevelInformation.delete_many({})

# login first
def reset_study_helper(deployment, study):
    SIMULATION_EMAIL=os.getenv('SIMULATION_EMAIL')
    SIMULATION_PASSWORD=os.getenv('SIMULATION_PASSWORD')
    url = 'http://localhost:20110/apis/auth/login'
    headers = {'Content-Type': 'application/json'}
    payload = {'email': SIMULATION_EMAIL, 'password': SIMULATION_PASSWORD}
    response = session.post(url, headers=headers, data=json.dumps(payload))

    headers = {'Content-Type': 'application/json'}
    payload = {'deployment': deployment, 'study': study}
    response = session.put("http://localhost:20110/apis/experimentDesign/resetStudy", headers=headers, data=json.dumps(payload))


def give_variable_value_helper(deployment, study, variableName, user, value):
    url = f'http://localhost:20110/apis/give_variable'
    headers = {'Content-Type': 'application/json'}
    payload = {'deployment': deployment, 'study': study, 'user': user, 'value': value, 'variableName': variableName}
    response = session.post(url, headers=headers, data=json.dumps(payload))

def assign_treatment_helper(deployment, study, user):
    url = f'http://localhost:20110/apis/get_treatment'
    headers = {'Content-Type': 'application/json'}
    payload = {'deployment': deployment, 'study': study, 'user': user}
    response = session.post(url, headers=headers, data=json.dumps(payload))
    return response.json()['treatment']['name']


def get_reward_helper(deployment, study, user, value):
    url = f'http://localhost:20110/apis/give_reward'
    headers = {'Content-Type': 'application/json'}
    payload = {'deployment': deployment, 'study': study, 'user': user, 'value': value}
    response = session.post(url, headers=headers, data=json.dumps(payload))


# Helpers to fake datatime.
from Analysis.AverageRewardByTime import AverageRewardByTime
import datetime
from Models.VariableValueModel import VariableValueModel
def fake_data_time(deployment, study):
    the_deployment = Deployment.find_one({"name": deployment})
    the_study = Study.find_one({"name": study, "deploymentId": the_deployment['_id']})
    mooclet_ids = list(
        MOOClet.find({"studyId": the_study['_id']}).distinct("_id")
    )
    the_interactions = list(Interaction.find({"moocletId": {"$in": mooclet_ids}}).sort("timestamp", pymongo.ASCENDING))
    # change the rewardTimestamp this way:
    # first 20% of the interactions, change the rewardTimestamp to four days ago.
    # second 20% of the interactions, change the rewardTimestamp to three days ago.
    # third 20% of the interactions, change the rewardTimestamp to two days ago.
    # fourth 20% of the interactions, change the rewardTimestamp to one day ago.
    # fifth 20% of the interactions, change the rewardTimestamp: no change.

    # create an array of 10 arrays
    time_mooclet_lists = [[] for i in range(10)]
    
    for i in range(0, len(the_interactions)):
        if the_interactions[i]['rewardTimestamp'] is None: continue
        time = datetime.datetime.now()
        if i < 0.1 * len(list(the_interactions)):
            time_mooclet_lists[9].append(the_interactions[i]['_id'])
            print("ihihihi")
        elif i < 0.2 * len(list(the_interactions)):
            time_mooclet_lists[8].append(the_interactions[i]['_id'])
        elif i < 0.3 * len(list(the_interactions)):
            time_mooclet_lists[7].append(the_interactions[i]['_id'])
        elif i < 0.4 * len(list(the_interactions)):
            time_mooclet_lists[6].append(the_interactions[i]['_id'])
        elif i < 0.5 * len(list(the_interactions)):
            time_mooclet_lists[5].append(the_interactions[i]['_id'])
        elif i < 0.6 * len(list(the_interactions)):
            time_mooclet_lists[4].append(the_interactions[i]['_id'])
        elif i < 0.7 * len(list(the_interactions)):
            time_mooclet_lists[3].append(the_interactions[i]['_id'])
        elif i < 0.8 * len(list(the_interactions)):
            time_mooclet_lists[2].append(the_interactions[i]['_id'])
        elif i < 0.9 * len(list(the_interactions)):
            time_mooclet_lists[1].append(the_interactions[i]['_id'])
        else:
            time_mooclet_lists[0].append(the_interactions[i]['_id'])

    for i in range(0, len(time_mooclet_lists)):
        print(len(time_mooclet_lists[i]))
        Interaction.update_many({"_id": {"$in": time_mooclet_lists[i]}}, {"$set": {"rewardTimestamp": datetime.datetime.now() - datetime.timedelta(days=i)}})


#fake_data_time('Simulations', 'case3')
# CASE1 (MAY NOT WORKING): 
def two_var_strong_predictor(num_users = 100):
    # The goal is to verify that Thompson sampling is better than uniform sampling, in terms of finding significant results, and average rewards (0 or 1 in this simple simulation case).
    # first, we define a N * 2 user matrix. The first column is the probablity that user will give reward 1 if they receive version 1, and the second column is the probablity that user will give reward 1 if they receive version 2.

    def generate_user_matrix(num_users):
        user_matrix = np.random.rand(num_users, 2)
        return user_matrix
    user_matrix = generate_user_matrix(num_users)
    # next, we need to have a dict that records the last version the user has received.
    users_status = {}
    # next, define all usernames
    users = []
    for user in range(1, num_users + 1):
        users.append(f'sim_user_{user}')
        name = f'sim_user_{user}'
        users_status[name] = "no_arm"

    # simulate user behaviour.

    def one_user(user, i):
        predictor = None
        for variable in variables:
            predictor = random.choice([0, 1])
            give_variable_value_helper(deployment, study, variable, user, predictor)
        while True:
            time.sleep(1) # every 2 seconds I pick a random user, assign arm or send reward.
            number = random.random()
            if number < 0.5: 
                pass
            else:
                if users_status[user] == "no_arm":
                    if random.random() < 0.9:
                        version_to_show = assign_treatment_helper(deployment, study, user)['name']
                        users_status[user] = version_to_show
                    else:
                        value = None
                        reward_prob = user_matrix[i][0] if users_status[user] == "version1" else user_matrix[i][1]

                        if users_status[user] == "version1" and predictor == 1:
                            reward_prob += 0.1
                        elif users_status[user] == "version2" and predictor == 1:
                            reward_prob -= 0.1
                        if random.random() < reward_prob:
                            value = 1
                        else:
                            value = 0
                        get_reward_helper(deployment, study, user, value)
                else:
                    if random.random() < 0.1:
                        version_to_show = assign_treatment_helper(deployment, study, user)['name']
                        users_status[user] = version_to_show
                    else:
                        value = None
                        reward_prob = user_matrix[i][0] if users_status[user] == "version1" else user_matrix[i][1]
                        if users_status[user] == "version1" and predictor == 1:
                            reward_prob += 0.15
                            reward_prob = np.min([reward_prob, 1])
                        elif users_status[user] == "version2" and predictor == 1:
                            reward_prob -= 0.15
                            reward_prob = np.max([reward_prob, 0])

                        if users_status[user] == "version1" and predictor == 0:
                            reward_prob -= 0.10
                            reward_prob = np.min([reward_prob, 1])
                        elif users_status[user] == "version2" and predictor == 0:
                            reward_prob += 0.10
                            reward_prob = np.max([reward_prob, 0])

                        if random.random() < reward_prob:
                            value = 1
                        else:
                            value = 0
                        get_reward_helper(deployment, study, user, value)
                        users_status[user] = "no_arm"



    for i in range(0, len(users)):
        user = users[i]
        t = threading.Thread(target=one_user, args=(user, i))
        t.start()



# CASE2:
def two_var_strong_predictor_async(deployment, study, num_users = 100, variables = ['gender']):
    reset_study_helper(deployment, study)

    # at this point, we know their gender.
    k = 0
    while k < num_users:
        user = str(k)
        predictor = None
        for variable in variables:
            # randomly get 0 or 1
            predictor = random.randint(0, 1)
            give_variable_value_helper(deployment, study, variable, user, predictor)
        #time.sleep(1) # every 2 seconds I pick a random user, assign arm or send reward.
        # get arm
        version_to_show = assign_treatment_helper(deployment, study, user)


        # give reward
        arm_indicator = 1 if version_to_show == "factor=1" else 0
        reward_prob = 0.4 + predictor * arm_indicator * 0.3 - arm_indicator * 0.2
        value = 1 if random.random() < reward_prob else 0
        if random.random() < reward_prob:
            get_reward_helper(deployment, study, user, value)
        else:
            get_reward_helper(deployment, study, user, value)

        k+=1

    fake_data_time(deployment, study)

    

# CASE3: THREE VERSIONS, ONE CONTEXTUAL, ONE STRONG PREDICTOR, TWO WEAK PREDICTORS
def run_case_three(deployment, study, num_devices = 100, num_users_per_device = 10, variables = []):
    reset_study_helper(deployment, study)
    # simulate user behaviour.

    # one thread
    def one_device(device, num_users_per_device):
        i = 0
        while i < num_users_per_device:
            user = device + "_" + str(i)
            #time.sleep(1) # every 2 seconds I pick a random user, assign arm or send reward.
            predictors = []
            for variable in variables:
                predictor = random.choice([0, 1])
                give_variable_value_helper(deployment, study, variable, user, predictor)
                predictors.append(predictor)
            
            # get a base reward probability
            reward_prob = random.random()

            # get an arm
            version_to_show = assign_treatment_helper(deployment, study, user)
            if predictors[0] == 0 and version_to_show == "version1":
                reward_prob += 0.2
            elif predictors[0] == 0 and version_to_show == "version2":
                reward_prob -= 0.2
            elif predictors[0] == 1 and version_to_show == "version1":
                reward_prob -= 0.1
            elif predictors[0] == 1 and version_to_show == "version2":
                reward_prob += 0.1

            reward = None
            if random.random() < reward_prob:
                reward = 1
            else:
                reward = 0
            get_reward_helper(deployment, study, user, reward)
            i += 1



    threads = []
    for i in range(0, num_devices):
        t = threading.Thread(target=one_device, args=(str(i), num_users_per_device))
        threads.append(t)
    for x in threads:
        x.start()
    for x in threads:
        x.join()
    fake_data_time(deployment, study)
    print("simulations done.")

num_devices = 200
num_users_per_device = 10
deployment = "Simulations"
study = "case3"
run_case_three(deployment = "Simulations", study = "case3", num_devices= num_devices, num_users_per_device = num_users_per_device, variables = ['gender', 'mood'])