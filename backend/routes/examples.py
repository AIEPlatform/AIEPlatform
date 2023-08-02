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
from Models.AssignerModel import AssignerModel
from Models.StudyModel import StudyModel
from Models.DeploymentModel import DeploymentModel
from Models.VariableModel import VariableModel
from errors import *
import traceback
from bson.objectid import ObjectId
import requests
import json

examples_apis = Blueprint('examples_apis', __name__)

# this is an example of how other app may intergrate AIEPlatform.

questions = [
    {
        "topic": "Confidence Intervals",
        "concept": 'https://statisticsbyjim.com/hypothesis-testing/confidence-interval/', 
        "question": "A random sample of 100 students was taken to estimate the mean score on a test. The sample mean is 75, and the sample standard deviation is 10. What is the 95% confidence interval for the population mean?", 
        "choices": ["(70.52, 79.48)", "(73.04, 76.96)", "(68.91, 81.09)", "(74.62, 76.38)"], 
        "right_answer_index": 1
    },
    {
        "topic": "Hypothesis Testing with Student-t Distribution",
        "concept": "https://www.britannica.com/science/Students-t-test", 
        "question": "A researcher wants to test the claim that the mean weight of a certain product is 500 grams. A sample of 25 products has a mean weight of 495 grams and a sample standard deviation of 12 grams. What is the calculated t-value for this hypothesis test?", 
        "choices": ["-2.08", "-1.67", "2.08", "1.67"], 
        "right_answer_index": 0
    },
    {
        "topic": "Mann-Whitney U Test",
        "concept": "https://datatab.net/tutorial/mann-whitney-u-test", 
        "question": "Two independent groups of students were given a test, and their scores are as follows:\n Group A: 78, 80, 82, 85, 88  \n Group B: 75, 77, 79, 81, 84 \n What is the calculated Mann-Whitney U statistic for comparing the distributions of these two groups?", 
        "choices": ["6", "12", "14", "21"], 
        "right_answer_index": 0
    },
    {
        "topic": "Deriving Cumulative Distribution Function",
        "concept": "https://stats.libretexts.org/Courses/Saint_Mary's_College_Notre_Dame/MATH_345__-_Probability_(Kuter)/4%3A_Continuous_Random_Variables/4.1%3A_Probability_Density_Functions_(PDFs)_and_Cumulative_Distribution_Functions_(CDFs)_for_Continuous_Random_Variables",
        "question": "Consider a probability density function (PDF) given by f(x) = 2x, where 0 ≤ x ≤ 1. Calculate the cumulative distribution function (CDF) F(x) for the given PDF.",
        "choices": ["F(x) = x^2", "F(x) = x^3", "F(x) = x^4", "F(x) = x^5"],
        "right_answer_index": 2
    },
    {
        "topic": "Understanding Beta-Bernoulli Posterior in Bandit Algorithm",
        "concept": "https://www.chrisstucchio.com/blog/2013/bayesian_bandit.html",
        "question": "In a bandit algorithm, a slot machine was played 100 times, resulting in 20 successes and 80 failures. What is the posterior distribution of the success probability using a Beta-Bernoulli model?",
        "choices": ["Beta(21, 81)", "Beta(25, 75)", "Beta(20, 80)", "Beta(30, 70)"],
        "right_answer_index": 0
    }
]


@examples_apis.route('/apis/pilotStudy/loadQuestion/<topic>', methods=['GET'])
def loadQuestion(topic):
    print(topic)
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
            # make an api to AIEPlatform to get reward.
            if choice == str(question['right_answer_index']):
                reward = 1
            url = "http://localhost:3000/apis/reward"
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
                    "message": "added", 
                    "score": reward
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