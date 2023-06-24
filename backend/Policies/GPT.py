import random
import datetime
from credentials import *
from Policies.policy import Policy
from Models.InteractionModel import InteractionModel
from Models.VariableValueModel import VariableValueModel
from Models.MOOCletModel import MOOCletModel
import openai

openai.api_key = 
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
	def choose_arm(self, user, where, other_information):
		# TODO: Check if consistent assignment!
		try:
			if 'messages' not in self.parameters:
				self.parameters['messages'] = []
				self.parameters['messages'].append({"role": "system", "content": self.parameters['initialPrompt']})
				MOOCletModel.update_policy_parameters(self._id, {'parameters': self.parameters})



			contextual_values = VariableValueModel.get_latest_variable_values(self.study['variables'], user)
			contextual_vars_dict = {}
			contextual_vars_id_dict = {}

			prompt = self.parameters['prompt']
			for contextual_value in contextual_values:
				print(contextual_value['value'])
				contextual_vars_dict[contextual_value['variableName']] = {"value": contextual_value['value'], "timestamp": contextual_value['timestamp']}
				contextual_vars_id_dict[contextual_value['variableName']] = contextual_value['_id']

				if contextual_value['variableName'] == "gender":
					prompt = prompt.replace("{gender}", str(contextual_value['value']))
			# only get version names
			versions = [version['name'] for version in self.study['versions']]
			
			prompt = prompt.replace("{versions}", str(versions))

			version_chosen = chatbot({"role": "user", "content": prompt}, self.parameters['messages'])
			print(version_chosen)
			lucky_version = None
			for version in self.study['versions']:
				if version['name'] in version_chosen:
					lucky_version = version
					break
			
			new_interaction = {
				"user": user,
				"treatment": lucky_version,
				"outcome": None,
				"where": where,
				"moocletId": self._id,
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
			MOOCletModel.update_policy_parameters(self._id, {'parameters': self.parameters})
			lock.release()
			return 200