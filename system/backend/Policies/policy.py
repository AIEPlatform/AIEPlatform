from abc import ABC, abstractmethod
from credentials import *
from Models.InteractionModel import InteractionModel
from errors import *
import threading
import time
from Models.LockModel import LockModel
import traceback
USER_CAN_WAIT_FOR_MODEL_UPDATE = 0.5
lock = threading.Lock()

from Models.StudyModel import StudyModel
class Policy(ABC):
	@staticmethod
	def validate_assigner(assigner):
		pass
	def __init__(self, user, **assigner_obj_from_db):
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

	def choose_arm(self, user, where, other_information, request_different_arm = False):
		with client.start_session() as session:
			session.start_transaction()
			someone_is_updating = False
			lock.acquire()
			# TODO: check if it prevents the lock being occupied infinitely.
			try:
				new_lock_id = self.check_lock(self._id, session)
			except Exception as e:
				print(e)
				print("error in check_lock")
				new_lock_id = None
			if new_lock_id is None:
				someone_is_updating = True
			lock.release()
			try:
				lucky_version = None
				if not someone_is_updating:
					p = threading.Thread(target=self.update_model, args=())
					p.start()
					start_time = time.time()
					while p.is_alive():
						if (time.time() - start_time) > USER_CAN_WAIT_FOR_MODEL_UPDATE:
							# Timeout reached, proceed without waiting
							break
						time.sleep(0.5)  # Adjust the sleep interval if needed
				lucky_version = self.choose_arm_algorithm(user, where, other_information, request_different_arm)
				LockModel.delete({"_id": new_lock_id}, session)
				session.commit_transaction()
				return lucky_version
			except Exception as e:
				print(e)
				LockModel.delete({"_id": new_lock_id}, session)
				session.abort_transaction()

	def check_lock(self, assignerId, session):
		# Check if lock exists
		try:
			lock_exists = LockModel.get_one({"assignerId": assignerId}, session)
			if lock_exists:
				return None
			else:
				# Create lock
				response = LockModel.create({"assignerId": assignerId}, session)
				return response.inserted_id
		except Exception as e:
			print(traceback.format_exc())
			return None

	@abstractmethod
	def choose_arm_algorithm(self, user, where, other_information, request_different_arm = False):
		pass

	def update_model(self):
		with client.start_session() as session:
			session.start_transaction()
			try:
				self.update_model_algorithm(session)
				session.commit_transaction()
			except Exception as e:
				session.abort_transaction()

	def update_model_algorithm(self, session):
		return
	
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
			if last_interaction is not None and last_interaction['outcome'] is None and last_interaction['treatment'] in self.study['versions']:
				return last_interaction['treatment']
			
		if not self.isConsistent: return None
		last_interaction = self.get_latest_interaction(user, where)
		if last_interaction is None and last_interaction['treatment'] in self.study['versions']:
			return None
		else:
			return last_interaction['treatment']


	def get_all_versions(self, user, where, request_different_arm = False):
		if not request_different_arm: return self.study['versions']
		else:
			# get all versions a user has been previously assigned to from Interaction.

			past_interactions = InteractionModel.get_interactions_for_where(self._id, user, where)
			assigned_versions = [interaction['treatment'] for interaction in past_interactions]
			if assigned_versions is None:
				return self.study['versions']
			else:
				unassigned_versions = [version for version in self.study['versions'] if version not in assigned_versions]
				return unassigned_versions