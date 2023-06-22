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

class TSConfigurable(Policy):
    def choose_arm(self, user, where, other_information):
        try:
            # TODO: We may need to remove the non-existing versions (that were deleted.)
            #import models individually to avoid circular dependency
            #no problem if missing data is random, but could
            #introduce bias if rewards are dont being sent is biased
            #suppose the reason they don't send reward is because they hate it and close survey
            #this skews for the subsequent batches. _could_ correct itself if we have the rewards come later
            #but this is also a general problem
            #note that using bernoulli for initial draws can be kind of problematic
            #because it's noisy and can result in imbalanced initial distributions
            #so we have more data about some arms than others
            #so maybe we could for batch 1 do evenly distributed as much as possible?
            # version_content_type = ContentType.objects.get_for_model(Version)
            #priors we set by hand - will use instructor rating and confidence in future
            # TODO : all explanations are having the same prior.

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

            #number of current participants within uniform random threshold, random sample
            if "uniform_threshold" in self.parameters and current_enrolled < self.parameters["uniform_threshold"]:
                lucky_version = random.choice(self.study['versions'])
                # # TODO: Make a new interaction. Remember to indicate this is from uniform.
                new_interaction = {
                    "user": user,
                    "treatment": lucky_version,
                    "outcome": None,
                    "where": where,
                    "moocletId": self._id,
                    "timestamp": datetime.datetime.now(),
                    "otherInformation": {'sampleMethod': 'uniform_random_cold_start'}, 
                    "contextuals": contextual_vars_dict,
                    "contextualIds": contextual_vars_id_dict
                }
                InteractionModel.insert_one(new_interaction)
                return lucky_version
            

            # check if epsilon exploration.

            if 'epsilon' in self.parameters and np.random.uniform() < self.parameters['epsilon']:
                lucky_version = random.choice(self.study['versions'])
                # # TODO: Make a new interaction. Remember to indicate this is from uniform.
                new_interaction = {
                    "user": user,
                    "treatment": lucky_version,
                    "outcome": None,
                    "where": where,
                    "moocletId": self._id,
                    "timestamp": datetime.datetime.now(),
                    "otherInformation": {'sampleMethod': 'epsilon_exploration'}, 
                    "contextuals": contextual_vars_dict,
                    "contextualIds": contextual_vars_id_dict
                }
                InteractionModel.insert_one(new_interaction)
                return lucky_version
            
            if True or 'tspostdiff_threshold'not in self.parameters or self.parameters['tspostdiff_threshold'] == 0:
                lucky_version = self.ts_sample()
                new_interaction = {
                    "user": user,
                    "treatment": lucky_version,
                    "outcome": None,
                    "where": where,
                    "moocletId": self._id,
                    "timestamp": datetime.datetime.now(),
                    "otherInformation": {"sampleMethod": "non-tspostdiff"}, 
                    "contextuals": contextual_vars_dict,
                    "contextualIds": contextual_vars_id_dict
                }

                InteractionModel.insert_one(new_interaction)
                return lucky_version
            else:
                lucky_version, sample_method = self.ts_postdiff_sample()
                new_interaction = {
                    "user": user,
                    "treatment": lucky_version,
                    "outcome": None,
                    "where": where,
                    "moocletId": self._id,
                    "timestamp": datetime.datetime.now(),
                    "otherInformation": {"sampleMethod": "tspostdiff"}, 
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
        

    # def ts_postdiff_sample(self, tspostdiff_thresh, versions_dict, context):
    #     """
    #     Inputs are a threshold and a dict of versions to successes and failures e.g.:
    #     {version1: {successess: 1, failures: 1}.
    #     version2: {successess: 1, failures: 1}, ...}
    #     """
    #     Variable = apps.get_model('engine', 'Variable')
    #     Value = apps.get_model('engine', 'Value')
    #     Version = apps.get_model('engine', 'Version')


    #     version_values = list(versions_dict.values())
    #     version_beta_1 = beta(version_values[0]["successes"], version_values[0]["failures"])
    #     version_beta_2 = beta(version_values[1]["successes"], version_values[1]["failures"])

    #     diff = abs(version_beta_1 - version_beta_2)

    #     #log whether was chosen by ts or ur
    #     ur_or_ts, created = Variable.objects.get_or_create(name="UR_or_TS")

    #     if diff < tspostdiff_thresh:# do UR
    #         # #print("choices to show")
    #         #print(context['mooclet'].version_set.all())
    #         version_to_show = list(versions_dict.keys())
    #         version_to_show = choice(version_to_show)
    #         #version_to_show = Version.objects.get(id=version_to_show)
    #         Value.objects.create(variable=ur_or_ts, value=0.0,
    #                             text="UR", learner=context["learner"], mooclet=context["mooclet"],
    #                             version=version_to_show)
    #         version_dict = model_to_dict(version_to_show)
    #         version_dict["selection_method"] = "uniform_random"
    #         return version_dict, "postdiff-uniform"

    #     else: #Do TS with resampling
    #         version_to_show = None
    #         max_beta = 0
    #         for version in versions_dict.keys():
    #             successes = versions_dict[version]["successes"]
    #             failures = versions_dict[version]["failures"]
    #             version_beta = beta(successes, failures)
    #             #print("pre max beta: " +str(max_beta))
    #             #print("version_beta: " + str(version_beta))
    #             if version_beta > max_beta:
    #                 max_beta = version_beta
    #                 version_to_show = version


    #         #log policy chosen
    #         Value.objects.create(variable=ur_or_ts, value=1.0,
    #                             text="TS", learner=context["learner"], mooclet=context["mooclet"],
    #                             version=version_to_show)

    #         version_dict = model_to_dict(version_to_show)
    #         version_dict["selection_method"] = "thompson_sampling_postdiff"
    #         return version_dict, "ts_postdiff"

    def ts_sample(self):
        """
        Input is a dict of versions to successes and failures e.g.:
        {version1: {successess: 1, failures: 1}.
        version2: {successess: 1, failures: 1}, ...}, and context
        """
        try:
            candidates = self.study['versions']
            current_posteriors = self.parameters["current_posteriors"]
            max_beta = 0
            for version in candidates:
                successes = current_posteriors[version['name']]["successes"] + self.parameters['prior']['successes']
                failures = current_posteriors[version['name']]["failures"] + self.parameters['prior']['failures']
                version_beta = beta(successes, failures)
                #print("pre max beta: " +str(max_beta))
                #print("version_beta: " + str(version_beta))
                if version_beta > max_beta:
                    max_beta = version_beta
                    version_to_show = version
            return version_to_show
        except Exception as e:
            #TODO: Send a default one, label it as callback.
            print(traceback.format_exc())
    

    def update_model(self, new_lock_id):
        #update policyparameters
        try:
            with client.start_session() as session:
                session.start_transaction()
                current_posteriors = {}
                min_rating, max_rating = self.parameters["min_rating"] if "min_rating" in self.parameters else 0, self.parameters['max_rating']
                for version in self.study['versions']:
                    # TODO: Verify Pan's guess on used_choose_group: this is to filter out the ratings that are from this MOOClet (policy), or from all policies of this study.

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