import random
import datetime
from credentials import *
from Policies.policy import Policy
class UniformRandom(Policy):
	def choose_arm(self, user, where, other_information):
		# TODO: Check if consistent assignment!
		try:
			lucky_version = self.get_consistent_assignment(user, where)
			if lucky_version is None:
				lucky_version = random.choice(self.study['versions'])
			new_interaction = {
				"user": user,
				"treatment": lucky_version,
				"outcome": None,
				"where": where,
				"moocletId": self._id,
				"timestamp": datetime.datetime.now(),
				"otherInformation": other_information
			}

			Interaction.insert_one(new_interaction)
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
			print("Giving reward...")
			Interaction.update_one({'_id': latest_interaction['_id']}, {'$set': {'outcome': value, 'rewardTimestamp': current_time}})
			return 200