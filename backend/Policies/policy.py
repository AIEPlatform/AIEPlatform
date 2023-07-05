from abc import ABC, abstractmethod
from credentials import *
from Models.InteractionModel import InteractionModel

from Models.StudyModel import StudyModel
class Policy(ABC):
	def __init__(self, user, **mooclet_obj_from_db):
		for key, value in mooclet_obj_from_db.items():
			setattr(self, key, value)

		# TODO: we shouldn't make any attribute special
		if 'reassignAfterReward' not in mooclet_obj_from_db:
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
	def choose_arm(self, user, where, other_information):
		pass
	@abstractmethod
	def get_reward(self, user, value, where, other_information):
		pass

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
