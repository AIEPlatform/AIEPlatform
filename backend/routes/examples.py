from credentials import *
from flask import Blueprint, session
from flask import request
from bson import json_util
from bson.objectid import ObjectId
from helpers import *
from Policies.UniformRandom import UniformRandom
from Policies.ThompsonSamplingContextual import ThompsonSamplingContextual
from Policies.TSConfigurable import TSConfigurable
from Policies.WeightedRandom import WeightedRandom
from Policies.GPT import GPT
import datetime
import time
import threading
from Models.VariableValueModel import VariableValueModel
from Models.InteractionModel import InteractionModel
from Models.MOOCletModel import MOOCletModel
from Models.StudyModel import StudyModel
from Models.DeploymentModel import DeploymentModel
from Models.VariableModel import VariableModel
from errors import *
import traceback
from bson.objectid import ObjectId
import requests
import json

examples_apis = Blueprint('examples_apis', __name__)

# this is an example of how other app may intergrate DataArrow.

questions = [
    {
        "topic": "Confidence Intervals",
        "concept": "A confidence interval is the mean of your estimate plus and minus the variation in that estimate.", 
        "question": "A random sample of 100 students was taken to estimate the mean score on a test. The sample mean is 75, and the sample standard deviation is 10. What is the 95% confidence interval for the population mean?", 
        "choices": ["(70.52, 79.48)", "(73.04, 76.96)", "(68.91, 81.09)", "(74.62, 76.38)"], 
        "right_answer_index": 0
    }
]


@examples_apis.route('/apis/pilotStudy/loadQuestion/<topic>', methods=['GET'])
def loadQuestion(topic):
    # find the question object from questions with the topic like the given one.
    for question in questions:
        if question['topic'] == topic:
            return json_util.dumps({
                "status": 200, 
                "question": question
            })
        
    return json_util.dumps({
        "status": 404, 
        "question": None
    })

@examples_apis.route('/apis/pilotStudy/giveReward', methods=['POST'])
def giveReward():
    # find the question object from questions with the topic like the given one.
    # load topic, username, where, and choice from the request.
    topic = request.json['topic']
    study = request.json['study']
    username = request.json['username']
    choice = request.json['choice']
    # find the question object from questions with the topic like the given one.
    for question in questions:
        if question['topic'] == topic:
            reward = 0
            # make an api to dataarrow to get reward.
            if choice == question['right_answer_index']:
                reward = 1
            url = "http://localhost:3000/apis/give_reward"
            payload = json.dumps({
            "deployment": "Pilot Study",
            "study": study,
            "user": username,
            "value": reward, 
            "where": topic
            })
            headers = {
            'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            print(response.json())

            return json_util.dumps({
                "status": 200, 
                "message": "added"
            })

        
    return json_util.dumps({
        "status": 404, 
        "message": "question not found"
    })
