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
	def choose_arm_algorithm(self, user, where, other_information, contextual_vars_dict, contextual_vars_id_dict, request_different_arm = False):
		# TODO: Check if consistent assignment!
		try:
			all_versions = self.get_all_versions(user, where, request_different_arm)
			if len(all_versions) == 0:
				raise NoDifferentTreatmentAvailable("There is no unassigned version left.")
			lucky_version = self.get_incomplete_consistent_assignment(user, where)
			if lucky_version is None:
				lucky_version = random.choice(all_versions)
			return lucky_version, None
		except Exception as e:
			print(e)
			return None