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

class DoubleBanditsMaximin(Policy):
    def __init__(self, user,  **mooclet_obj_from_db):
        
        super().__init__(user, **mooclet_obj_from_db)
        self.parameters['K'] = len(self.study['versions'])
        self.parameters['Bmatrix'] = np.zeros(self.parameters['K'],self.parameters['K'] )

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

            #number of current participants within uniform random threshold, random sample


            first_action_num, second_action_num = self.DoubleSample()
            first_action = self.study['versions'][first_action_num] 
            second_action = self.study['versions'][second_action_num]

            lucky_version = first_action #Given that we can only display one action, I am returning the first one

            new_interaction = {
                "user": user,
                "treatment 1": first_action,
                "treatment 2": second_action,
                "outcome": None,
                "where": where,
                "moocletId": self._id,
                "timestamp": datetime.datetime.now(),
                "otherInformation": {"sampleMethod": "dueling bandits maximin"}, 
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
    
    
    def DoubleSample(self):
        current_time = datetime.datetime.now()
        try:
            
            
            # Sample theta values
            Bmatrix = self.parameters["Bmatrix"] 
            K = self.parameters['K']

            theta_sample_one = np.zeros(K, K)
            theta_sample_two = np.zeros((K, K))


            # Diagonals should all be 1/2
            np.fill_diagonal(theta_sample_one, 0.5)
            np.fill_diagonal(theta_sample_two, 0.5)

            #TODO:Pan says this we don't need to worry about the indices at this point
            for i in range(0,K):
                for j in range(0,K):
                    if i < j:
                        theta_sample_one[i][j] = beta(Bmatrix[i][j],Bmatrix[j][i])
                        theta_sample_one[j][i] = 1 - theta_sample_one[i][j]
                        theta_sample_two[i][j] = beta(Bmatrix[i][j],Bmatrix[j][i])
                        theta_sample_two[j][i] = 1 - theta_sample_two[i][j]
            # Find first treatment I
            maximin_dict = {}
            for i in range(0,K):
                maximin_dict[i] = theta_sample_one[i][0]
                for j in range(0,K):
                    maximin_dict[i] = min(maximin_dict[i], theta_sample_one[i][j])

            maximin_value = max(maximin_dict.values())
            options = [key for key, value in maximin_dict.items() if value == maximin_value]
            first_action = random.choice(options)

            # Find second treatment J
            maximin_dict = {}
            for j in range(0,K):
                maximin_dict[j] = theta_sample_two[j][0]
                for i in range(0,K):
                    maximin_dict[j] = min(maximin_dict[j], theta_sample_two[j][i])

            maximin_value = max(maximin_dict.values())
            options = [key for key, value in maximin_dict.items() if value == maximin_value]
            second_action = random.choice(options)
    
            return first_action,second_action
        except Exception as e:
            #TODO: Send a default one, label it as callback.
            print(traceback.format_exc())
    

    def update_model(self, new_lock_id):
        current_time = datetime.datetime.now()

        with client.start_session() as session:
            session.start_transaction()
            try:
                pref_matrix_estimate = self.parameters["Bmatrix"] 
                interactions_for_B_matrix = InteractionModel.use_unused_interactions(self._id, None, session=session)
                # TODO: I am assuming outcome is 1 or 0, where for i < j 1 when users prefers i to j, and 0 otherwise
                numpy_preferences = np.array([interaction['outcome'] for interaction in interactions_for_B_matrix])
                for interaction in interactions_for_B_matrix:
                    #Find the correct i,j index values for the treatments.
                    i = self.parameters['versions'].search(interaction["treatment 1"])
                    j = self.parameters['versions'].search(interaction["treatment 2"])
                    pref_matrix_estimate[i][j] += interaction["outcome"]
                    pref_matrix_estimate[j][i] += 1 - interaction["outcome"]

                # Update the estimate of the preference matrx
                print("New Prefernce Matrix Estimate: ")
                print(pref_matrix_estimate)
                MOOCletModel.update_policy_parameters(self._id, {"parameters.Bmatrix": pref_matrix_estimate,
                                                                  "updatedAt": datetime.datetime.now()})
                self.parameters["Bmatrix"] = pref_matrix_estimate

                # Release lock.
                session.commit_transaction()
                print(f'group model updated successfully! Time spent: {(datetime.datetime.now() - current_time).total_seconds()} seconds')
                self.parameters = MOOCletModel.find_mooclet({"_id": self._id})['parameters']
                self.reinit()
                LockModel.delete({"_id": new_lock_id})
                return
            except Exception as e:
                print(e)
                print(f'model update failed, rollback...')
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