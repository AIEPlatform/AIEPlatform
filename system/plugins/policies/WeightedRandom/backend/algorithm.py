import random
import datetime
from credentials import *
from Policies.policy import Policy
from Models.InteractionModel import InteractionModel
from Models.VariableValueModel import VariableValueModel
from errors import *
from errors import *
class WeightedRandom(Policy):
    # TODO
    # make a static method called validate assigner.
    @staticmethod
    def validate_assigner(assigner):
        # check if cov matrix and mean are numeric.
        try:
            # assigner['parameters'] is a dictionary. I want to convert all values to float.
            assigner['parameters'] = {key: float(value) for key, value in assigner['parameters'].items()}
        except ValueError as e:
            raise ValueError("Invalid numeric string found in the weights") from e
        
        return assigner
    
    def choose_arm_algorithm(self, user, where, other_information, contextual_vars_dict, contextual_vars_id_dict, request_different_arm = False):
        # TODO: Check if consistent assignment!
        try:
            all_versions = self.get_all_versions(user, where, request_different_arm)
            if len(all_versions) == 0:
                raise NoDifferentTreatmentAvailable("There is no unassigned version left.")

            lucky_version = self.get_incomplete_consistent_assignment(user, where)
            if lucky_version is None:
                keys = list(self.parameters.keys())
                weights = list(self.parameters.values())
                drawn_key = random.choices(keys, weights)[0]
                for version in all_versions:
                    if version['name'] == drawn_key:
                        lucky_version = version
                        break
            return lucky_version, None
        except Exception as e:
            print(e)
            return None