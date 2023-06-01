deployment = 'test'
study = 'sim'
num_users = 20
import time
import random
from adexacc import *
users = []
users_status = {}
for user in range(1, num_users + 1):
    users.append(f'sim_user_{user}')
    name = f'sim_user_{user}'
    users_status[name] = "no_arm"

while True:
    time.sleep(1) # every 2 seconds I pick a random user, assign arm or send reward.
    user = random.choice(users)
    if users_status[user] == "no_arm":
        if random.random() < 0.95:
            assign_treatment(deployment, study, user)
            users_status[user] = "arm_assigned"
        else:
            value = random.choice([0, 1])
            get_reward(deployment, study, user, value)
            users_status[user] = "no_arm"
    else:
        if random.random() < 0.3:
            assign_treatment(deployment, study, user)
            users_status[user] = "arm_assigned"
        else:
            value = random.choice([0, 1])
            get_reward(deployment, study, user, value)
            users_status[user] = "no_arm"


for user in users:
    assign_treatment(deployment, study, user)