import random
import datetime
from credentials import *
from Policies.policy import Policy
from Models.InteractionModel import InteractionModel
from Models.VariableValueModel import VariableValueModel
from errors import *
class UniformRandom(Policy):

	@staticmethod
	def validate_assigner(assigner):
		return assigner
	def choose_arm_algorithm(self, user, where, other_information, request_different_arm = False):
		# TODO: Check if consistent assignment!
		try:
			all_versions = self.get_all_versions(user, where, request_different_arm)
			if len(all_versions) == 0:
				raise NoDifferentTreatmentAvailable("There is no unassigned version left.")
			lucky_version = self.get_incomplete_consistent_assignment(user, where)
			if lucky_version is None:
				lucky_version = random.choice(all_versions)

			contextual_values = VariableValueModel.get_latest_variable_values(self.study['variables'], user)
			contextual_vars_dict = {}
			contextual_vars_id_dict = {}

			for contextual_value in contextual_values:
				print(contextual_value['value'])
				contextual_vars_dict[contextual_value['variable']] = {"value": contextual_value['value'], "timestamp": contextual_value['timestamp']}
				contextual_vars_id_dict[contextual_value['variable']] = contextual_value['_id']


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