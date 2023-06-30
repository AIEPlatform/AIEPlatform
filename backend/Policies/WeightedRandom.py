import random
import datetime
from credentials import *
from Policies.policy import Policy
from Models.InteractionModel import InteractionModel
from Models.VariableValueModel import VariableValueModel
class WeightedRandom(Policy):
    def choose_arm(self, user, where, other_information):
        # TODO: Check if consistent assignment!
        try:
                    
            # TODO: what if a version is deleted?

            contextual_values = VariableValueModel.get_latest_variable_values(self.study['variables'], user)
            contextual_vars_dict = {}
            contextual_vars_id_dict = {}

            for contextual_value in contextual_values:
                print(contextual_value['value'])
                contextual_vars_dict[contextual_value['variableName']] = {"value": contextual_value['value'], "timestamp": contextual_value['timestamp']}
                contextual_vars_id_dict[contextual_value['variableName']] = contextual_value['_id']


            lucky_version = self.get_consistent_assignment(user, where)
            if lucky_version is None:
                keys = list(self.parameters.keys())
                weights = list(self.parameters.values())
                drawn_key = random.choices(keys, weights)[0]
                for version in self.study['versions']:
                    if version['name'] == drawn_key:
                        lucky_version = version
                        break

            new_interaction = {
                "user": user,
                "treatment": lucky_version,
                "outcome": None,
                "where": where,
                "moocletId": self._id,
                "timestamp": datetime.datetime.now(),
                "otherInformation": other_information,
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