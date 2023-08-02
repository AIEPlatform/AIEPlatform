from abc import ABC, abstractmethod
from credentials import *
from Models.InteractionModel import InteractionModel
from errors import *

from Models.StudyModel import StudyModel
class Policy(ABC):
	def __init__(self, user, **assigner_obj_from_db):
		print(assigner_obj_from_db)
		for key, value in assigner_obj_from_db.items():
			setattr(self, key, value)

		# TODO: we shouldn't make any attribute special
		if 'reassignAfterReward' not in assigner_obj_from_db:
			self.reassignAfterReward = False

		study = StudyModel.get_one(
			{
				"_id": self.studyId
			}, 
			public = True
		)
		self.study = study
		self.user = user

	@abstractmethod
	def choose_arm(self, user, where, other_information, request_different_arm = False):
		pass

	def get_reward(self, user, value, where, other_information):

		latest_interaction = self.get_latest_interaction(user, where)
		if latest_interaction is None:
			raise OrphanReward("There is no interaction this reward to be appended to.") 
		else:
			InteractionModel.append_reward(latest_interaction['_id'], value)
			return 200

	def get_latest_interaction(self, user, where):
		last_interaction = InteractionModel.get_latest_interaction_for_where(self._id, user, where)
		if last_interaction is None or last_interaction['outcome'] is not None:
			return None
		else:
			return last_interaction
		
	def get_incomplete_consistent_assignment(self, user, where):
		if self.reassignAfterReward:
			# check if the latest one is an incomplete one. #TODO: does it make sure that there won't be any incomplete one in previous interactions??
			last_interaction = self.get_latest_interaction(user, where)
			if last_interaction is not None and last_interaction['outcome'] is None:
				return last_interaction['treatment']
			
		if not self.isConsistent: return None
		last_interaction = self.get_latest_interaction(user, where)
		if last_interaction is None:
			return None
		else:
			return last_interaction['treatment']


	def get_all_versions(self, user, where, request_different_arm = False):
		if not request_different_arm: return self.study['versions']
		else:
			# get all versions a user has been previously assigned to from Interaction.

			past_interactions = InteractionModel.get_interactions_for_where(self._id, user, where)
			assigned_versions = [interaction['treatment'] for interaction in past_interactions if interaction['outcome'] is None]
			if assigned_versions is None:
				return self.study['versions']
			else:
				unassigned_versions = [version for version in self.study['versions'] if version not in assigned_versions]
				return unassigned_versions