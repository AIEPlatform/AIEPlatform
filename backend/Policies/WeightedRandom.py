import random
import datetime
from credentials import *
from Policies.policy import Policy
from Models.InteractionModel import InteractionModel
from Models.VariableValueModel import VariableValueModel
class WeightedRandom(Policy):
    def choose_arm(self, user, where, other_information, request_different_arm = False):
        # TODO: Check if consistent assignment!
        try:
            all_versions = self.get_all_versions(user, where, request_different_arm)
            if len(all_versions) == 0:
                raise NoDifferentTreatmentAvailable("There is no unassigned version left.")
            # TODO: what if a version is deleted?

            contextual_values = VariableValueModel.get_latest_variable_values(self.study['variables'], user)
            contextual_vars_dict = {}
            contextual_vars_id_dict = {}

            for contextual_value in contextual_values:
                contextual_vars_dict[contextual_value['variableName']] = {"value": contextual_value['value'], "timestamp": contextual_value['timestamp']}
                contextual_vars_id_dict[contextual_value['variableName']] = contextual_value['_id']


            lucky_version = self.get_incomplete_consistent_assignment(user, where)
            if lucky_version is None:
                keys = list(self.parameters.keys())
                weights = list(self.parameters.values())
                drawn_key = random.choices(keys, weights)[0]
                for version in all_versions:
                    if version['name'] == drawn_key:
                        lucky_version = version
                        break

            new_interaction = {
                "user": user,
                "treatment": lucky_version,
                "outcome": None,
                "where": where,
                "assignerId": self._id,
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