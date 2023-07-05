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
    },
    {
        "topic": "Hypothesis Testing with Student-t Distribution",
        "concept": "Student's t-test, in statistics, a method of testing hypotheses about the mean of a small sample drawn from a normally distributed population when the population standard deviation is unknown. In 1908 William Sealy Gosset, an Englishman publishing under the pseudonym Student, developed the t-test and t distribution.", 
        "question": "A researcher wants to test the claim that the mean weight of a certain product is 500 grams. A sample of 25 products has a mean weight of 495 grams and a sample standard deviation of 12 grams. What is the calculated t-value for this hypothesis test?", 
        "choices": ["-2.08", "-1.67", "2.08", "1.67"], 
        "right_answer_index": 2
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

            response = requests.request("POST", url, headers=headers, data=payload).json()

            if response["status_code"] == 200:
                return json_util.dumps({
                    "status_code": 200, 
                    "message": "added"
                })
            else:
                return json_util.dumps({
                    "status_code": 400, 
                    "message": "not added"
                })


        
    return json_util.dumps({
        "status_code": 404, 
        "message": "question not found"
    })




@examples_apis.route('/apis/pilotStudy/checkDoneOrNot', methods=['GET'])
def check_done_or_not():
    # find the question object from questions with the topic like the given one.
    # load topic, username, where, and choice from the request.
    # load from params
    try:
        done = False
        topic = request.args.get('topic')
        study = request.args.get('study')
        username = request.args.get('username')

        # make use of the api.
        url = "http://localhost:3000/apis/integration/findUserInteractions?deployment=Pilot Study&study=" + study + "&user=" + username + "&where=" + topic
        response = requests.request("GET", url)
        if response.status_code == 200:
            j = response.json()
            interactions = j['interactions']
            if len(interactions) > 0:
                for interaction in interactions:
                    if interaction['outcome'] is not None:
                        done = True
                        break
            return json_util.dumps({
                "status_code": 200, 
                "done": done
            })
    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500, 
            "message": "error"
        })