import random
from credentials import *
import os
# load config from config.json
import json
with open('config.json', 'r') as f:
    config = json.load(f)

import openai

def random_by_weight(options):
    # options is a list of dict {..., weight: weight}
    total_weight = sum(element["weight"] for element in options)

    # Generate a list of weights for random.choices()
    weights = [element["weight"] / total_weight for element in options]

    # Randomly select an element based on weights
    selected_element = random.choices(options, weights=weights, k=1)[0]
    return selected_element

# this function modify the lucky_version content by making an api call to the ai service
# originally, the lucky_version content is the prompt to be sent.
def generate_content_ai(lucky_version):
    # check if OPEN_AI_KEY exists in config and is not null.

    if 'OPEN_AI_KEY' not in config or config['OPEN_AI_KEY'] is None:
        return lucky_version
    
    OPEN_AI_KEY = config['OPEN_AI_KEY']
    prompt = lucky_version['content']
    # make api call to the ai service
    openai.api_key = config["OPEN_AI_KEY"]

    def chatbot(input, messages):
        if input:
            messages.append(input)
            chat = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages
            )
            reply = chat.choices[0].message.content
            messages.append({"role": "assistant", "content": reply})
            return reply

    version_chosen = chatbot({"role": "user", "content": prompt}, [])

    lucky_version['content'] = version_chosen

    return lucky_version
