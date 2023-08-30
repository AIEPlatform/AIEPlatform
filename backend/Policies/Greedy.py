import random
import datetime
from credentials import *
from Policies.policy import Policy
from numpy.random import choice, beta
import numpy as np
from scipy.stats import invgamma
from helpers import *
from multiprocessing import Process
import os
import time
import threading
from impute import *
import traceback
import sys
from Models.VariableValueModel import VariableValueModel
from Models.InteractionModel import InteractionModel
from Models.MOOCletModel import MOOCletModel
from Models.LockModel import LockModel



USER_CAN_WAIT_FOR_MODEL_UPDATE = 0.5
lock = threading.Lock()

class Greedy(Policy):
    def choose_arm(self, user, where, other_information):
        try:
            if "batch_size" in self.parameters:
                batch_size = self.parameters["batch_size"]

            current_enrolled = InteractionModel.get_num_participants_for_assigner(self._id)
            # TODO: need to force batch_size not be 0.
            if batch_size ==0: 
                batch_size = 1
            if "current_posteriors" not in self.parameters or current_enrolled % batch_size == 0:
                print("check if this group needs model to be updated")
                someone_is_updating = False
                lock.acquire()
                print(f'{user} checking lock...')
                # TODO: check if it prevents the lock being occupied infinitely.
                try:
                    new_lock_id = check_lock(self._id)
                except Exception as e:
                    print(e)
                    print("error in check_lock")
                    new_lock_id = None
                if new_lock_id is None:
                    someone_is_updating = True
                    print(f'{user} finds someone\'s updating the model...')
                lock.release()
                if not someone_is_updating:
                    print(f'{user} updating model..')
                    p = threading.Thread(target=self.update_model, args=(new_lock_id, ))
                    p.start()
                    start_time = time.time()
                    while p.is_alive():
                        if (time.time() - start_time) > USER_CAN_WAIT_FOR_MODEL_UPDATE:
                            # Timeout reached, proceed without waiting
                            break
                        time.sleep(0.5)  # Adjust the sleep interval if needed
                self.update_model(new_lock_id)

            # Get the variables associated with this study.
            contextual_values = VariableValueModel.get_latest_variable_values(self.study['variables'], user)
            contextual_vars_dict = {}
            contextual_vars_id_dict = {}
            for contextual_value in contextual_values:
                contextual_vars_dict[contextual_value['variableName']] = {"value": contextual_value['value'], "timestamp": contextual_value['timestamp']}
                contextual_vars_id_dict[contextual_value['variableName']] = contextual_value['_id']


            # check if epsilon exploration.

            if 'epsilon' in self.parameters and np.random.binomial(size=1,n=1,p=(1-self.parameters['epsilon']))[0] == 1:
                lucky_version = random.choice(self.study['versions'])

                 # Notice sampleMethod is named 'uniform_random' rather than 'greedy'
                new_interaction = {
                    "user": user,
                    "treatment": lucky_version,
                    "outcome": None,
                    "where": where,
                    "moocletId": self._id,
                    "timestamp": datetime.datetime.now(),
                    "otherInformation": {'sampleMethod': 'uniform_random'},
                    "contextuals": contextual_vars_dict,
                    "contextualIds": contextual_vars_id_dict
                }
                InteractionModel.insert_one(new_interaction)
                return lucky_version
            else:
                lucky_version = self.greedy_sample()
                new_interaction = {
                    "user": user,
                    "treatment": lucky_version,
                    "outcome": None,
                    "where": where,
                    "moocletId": self._id,
                    "timestamp": datetime.datetime.now(),
                    "otherInformation": {"sampleMethod": "greedy"}, 
                    "contextuals": contextual_vars_dict,
                    "contextualIds": contextual_vars_id_dict
                }

                InteractionModel.insert_one(new_interaction)
                return lucky_version


        except Exception as e:
            print(e)
            return None

    def get_reward(self, user, value, where, other_information):
        current_time = datetime.datetime.now()
        latest_interaction = self.get_latest_interaction(user, where)
        if latest_interaction is None:
            return 400
        else:
            InteractionModel.append_reward(latest_interaction['_id'], value)
            return 200

    def greedy_sample(self):
        try:
            candidates = self.study['versions']
            current_posteriors = self.parameters["current_posteriors"]
            max_mean = 0
            for version in candidates:
                successes = current_posteriors[version['name']]["successes"]
                failures = current_posteriors[version['name']]["failures"]
                version_mean = successes / (successes + failures)

                if version_mean > max_mean:
                    max_mean = version_mean
                    version_to_show = version
            return version_to_show
        except Exception as e:
            print(traceback.format_exc())
    
    

    def update_model(self, new_lock_id):
        #update policyparameters
        try:
            with client.start_session() as session:
                session.start_transaction()
                current_posteriors = {}
                min_rating, max_rating = self.parameters["min_rating"] if "min_rating" in self.parameters else 0, self.parameters['max_rating']
                for version in self.study['versions']:

                    if "used_choose_group" in self.parameters and self.parameters["used_choose_group"] == True:
                        student_ratings = InteractionModel.get_mooclet_outcome_by_version(self._id, version)
                    else:
                        student_ratings = list(InteractionModel.get_study_outcome_by_version(self.study["_id"], version))

                    if len(student_ratings) > 0:
                        student_ratings = np.array(student_ratings)
                        rating_count = len(student_ratings)
                        sum_rewards = np.sum(student_ratings)
                    else:
                        rating_count = 0
                        sum_rewards = 0
                    success_update = (sum_rewards - rating_count * min_rating) / (max_rating - min_rating)
                    successes = success_update
                    failures = rating_count - success_update
                    current_posteriors[version['name']] = {"successes":successes, "failures": failures}

                print("new posteriors: ")
                print(current_posteriors)
                MOOCletModel.update_policy_parameters(self._id, {"parameters.current_posteriors": current_posteriors, "updatedAt": datetime.datetime.now()})
                self.parameters["current_posteriors"] = current_posteriors
                session.commit_transaction()
                LockModel.delete({"_id": new_lock_id})
        except Exception as e:
            print("update model fail.")
            print(traceback.format_exc())
            LockModel.delete({"_id": new_lock_id})
            session.abort_transaction()
            return
        

def check_lock(moocletId):
    # Check if lock exists
    try:
        lock_exists = LockModel.get_one({"moocletId": moocletId})
        if lock_exists:
            return None
        else:
            # Create lock
            response = LockModel.create({"moocletId": moocletId})
            return response.inserted_id
    except Exception as e:
        print(e)
        return None