import random
import datetime
from credentials import *
from Policies.policy import Policy
from Models.InteractionModel import InteractionModel
from Models.VariableValueModel import VariableValueModel
from Models.AssignerModel import AssignerModel
import openai
from errors import *

import json
with open('config.json', 'r') as f:
    config = json.load(f)

openai.api_key = config["OPEN_AI_KEY"]

import threading
lock = threading.Lock()

def chatbot(input, messages):
    if input:
        messages.append(input)
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
        reply = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        return reply
    
class GPT(Policy):
	# parameters: {
    # prompt: "", 
    # lastK: ""}

    # TODO
    # make a static method called validate assigner.
	@staticmethod
	def validate_assigner(assigner):
		return assigner
    
	def choose_arm(self, user, where, other_information, contextual_vars_dict, contextual_vars_id_dict, request_different_arm = False):
		# TODO: Check if consistent assignment!
		all_versions = self.get_all_versions(user, where, request_different_arm)
		if len(all_versions) == 0:
			raise NoDifferentTreatmentAvailable("There is no unassigned version left.")
		try:
			if 'messages' not in self.parameters:
				self.parameters['messages'] = []
				self.parameters['messages'].append({"role": "system", "content": self.parameters['initialPrompt']})
				AssignerModel.update_policy_parameters(self._id, {'parameters': self.parameters})


			# TODO: GPT should be able to handle contextual variables.


			# contextual_values = VariableValueModel.get_latest_variable_values(self.study['variables'], user)
			# contextual_vars_dict = {}
			# contextual_vars_id_dict = {}

			# prompt = self.parameters['prompt']
			# for contextual_value in contextual_values:
			# 	contextual_vars_dict[contextual_value['variable']] = {"value": contextual_value['value'], "timestamp": contextual_value['timestamp']}
			# 	contextual_vars_id_dict[contextual_value['variable']] = contextual_value['_id']

			# 	if contextual_value['variable'] == "gender":
			# 		prompt = prompt.replace("{gender}", str(contextual_value['value']))
			# only get version names
			versions = [version['name'] for version in all_versions]
			
			prompt = prompt.replace("{versions}", str(versions))

			version_chosen = chatbot({"role": "user", "content": prompt}, self.parameters['messages'])
			lucky_version = None
			for version in all_versions:
				if version['name'] in version_chosen:
					lucky_version = version
					break
			if lucky_version is None:
				# do unifoirm
				lucky_version = random.choice(all_versions)
			
			return lucky_version, None
		except Exception as e:
			print(e)
			lucky_version = random.choice(all_versions)
			return lucky_version, {"gptError": True}
		
	def get_reward(self, user, value, where, other_information):
		current_time = datetime.datetime.now()
		latest_interaction = self.get_latest_interaction(user, where)
		if latest_interaction is None:
			return 400
		else:
			lock.acquire()
			InteractionModel.append_reward(latest_interaction['_id'], value)
			prompt_to_add = f'This is a new feedback: a person who has gender = {str(latest_interaction["contextuals"]["gender"]["value"])} gives reward {str(value)} on {latest_interaction["treatment"]["name"]}'
			self.parameters['messages'].append({"role": "system", "content": prompt_to_add})
			AssignerModel.update_policy_parameters(self._id, {'parameters': self.parameters})
			lock.release()
			return 200