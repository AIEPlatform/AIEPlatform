from abc import ABC, abstractmethod
from credentials import *
from Models.InteractionModel import InteractionModel
from errors import *
import threading
import time
from Models.LockModel import LockModel
from Models.VariableValueModel import VariableValueModel
from impute import random_imputation
import traceback
import datetime
from helpers import *
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
				contextual_vars_dict, contextual_vars_id_dict = self.get_or_impute_contextuals(user, where)
				lucky_version, extra_info = self.choose_arm_algorithm(user, where, other_information, contextual_vars_dict, contextual_vars_id_dict, request_different_arm)


				# check if AIContent is true.
				if 'AIContent' in self.study and self.study['AIContent']:
					lucky_version = generate_content_ai(lucky_version)

				# Insert new interaction
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

				# extra_info is a dictionary or None
				if extra_info is not None:
					new_interaction.update(extra_info)

				InteractionModel.insert_one(new_interaction)
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
	def choose_arm_algorithm(self, user, where, other_information, contextual_vars_dict, contextual_vars_id_dict, request_different_arm = False):
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
		if last_interaction is None or last_interaction['treatment'] not in self.study['versions']:
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
			
	def get_or_impute_contextuals(self, user, where):
		current_time = datetime.datetime.now()
		contextual_vars = self.study['variables']
		# Get the contextual variables for the learner (most recent ones), or auto init ones.
		
		result = VariableValueModel.get_latest_variable_values(contextual_vars, user)
		
		# Iterate over the array list
		for value in contextual_vars:
			has_document = False

			# Check if a document exists for the current value
			for document in result:
				if document['variable'] == value:
					has_document = True
					break

			
			imputed_value = random_imputation(value) # TODO: in the future we need to check the Assigner's configuration to see which imputer to use.

			# Insert a document into the other collection if no document exists
			# get deployment_name

			the_deployment = Deployment.find_one({"_id": self.study['deploymentId']})
			if not has_document:
				document_to_insert = {
					'deployment': the_deployment['name'],
					"variable": value, 
					'value': imputed_value,   # TODO: impute based on a better rule.
					'user': user,
					'where': 'auto init', 
					'timestamp': current_time
				}
				VariableValueModel.insert_variable_value(document_to_insert)
			
		contextual_values = VariableValueModel.get_latest_variable_values(contextual_vars, user)

		contextual_vars_dict = {}
		contextual_vars_id_dict = {}

		for contextual_value in contextual_values:
			contextual_vars_dict[contextual_value['variable']] = {"value": contextual_value['value'], "timestamp": contextual_value['timestamp']}
			contextual_vars_id_dict[contextual_value['variable']] = contextual_value['_id']

		return contextual_vars_dict, contextual_vars_id_dict
			