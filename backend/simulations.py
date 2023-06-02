deployment = 'test'
study = 'sim'
variable = 'test variable'
num_users = 1000
import time
import random
from adexacc import *
users = []
users_status = {}
import threading
from credentials import *

Lock.delete_many({})
# {"studyName":"sim","description":"test2 description","mooclets":[{"id":1,"parent":0,"droppable":true,"isOpen":true,"text":"mooclet1","name":"mooclet1","policy":"UniformRandom","parameters":{},"weight":100},{"id":2,"parent":1,"droppable":true,"isOpen":true,"text":"mooclet2","name":"mooclet2","policy":"UniformRandom","parameters":{},"weight":100},{"id":3,"parent":1,"droppable":true,"isOpen":true,"text":"mooclet3","name":"mooclet3","policy":"ThompsonSamplingContextual","parameters":{"batch_size":1,"variance_a":1,"variance_b":2,"uniform_threshold":1,"precision_draw":1,"updatedPerMinute":3,"include_intercept":true,"coef_cov":[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],"coef_mean":[0,0,0,0],"regressionFormulaItems":[[{"name":"test variable","index":0}],[{"name":"version1","content":"version 1"}],[{"name":"test variable","index":0},{"name":"version1","content":"version 1"}]]},"weight":100}],"variables":[{"name":"test variable","index":0}],"versions":[{"name":"version1","content":"version 1"},{"name":"version2","content":"version 2"}]}

for user in range(1, num_users + 1):
    users.append(f'sim_user_{user}')
    name = f'sim_user_{user}'
    users_status[name] = "no_arm"

def one_user(user):
    while True:
        time.sleep(1) # every 2 seconds I pick a random user, assign arm or send reward.
        number = random.random()
        if number < 0.5: 
            pass
        elif number >= 0.5 and number < 0.95:
            if users_status[user] == "no_arm":
                if random.random() < 0.9:
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
        else:
            # contextual
            new_value = random.choice([0, 1])
            give_variable_value(variable, user, new_value)




for user in users:
    t = threading.Thread(target=one_user, args=(user,))
    t.start()