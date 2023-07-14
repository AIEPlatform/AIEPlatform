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

user_interaction_apis = Blueprint('user_interaction_apis', __name__)

def create_mooclet_instance(user, the_mooclet):
    cls = globals().get(the_mooclet['policy'])
    if cls:
        return cls(user, **the_mooclet)
    else:
        raise ValueError(f"Invalid policy name")
    
def inductive_get_mooclet(mooclet, user):
    if len(mooclet['children']) > 0:
        children = MOOCletModel.find_mooclets({"_id": {"$in": mooclet['children']}}, {"_id": 1, "weight": 1})
        # TODO: Check previous assignment. Choose MOOClet should be consistent with previous assignment.
        next_mooclet_id = random_by_weight(list(children))['_id']
        next_mooclet = MOOCletModel.find_mooclet({'_id': next_mooclet_id})
        return inductive_get_mooclet(next_mooclet, user)
    else:
        # this is a leaf node. return it!
        return mooclet

def get_mooclet_for_user(study, user):
    # Note that, a deployment + study_name + user uniquely identify a mooclet.
    # OR, this function will decide one and return.
    # TODO: Check if re-assignment is needed. For example, the mooclet is deleted (not yet implemented), or the experiment requires re-assignment at a certain time point.
    # Find the latest interaction.
    the_interaction = InteractionModel.find_last_interaction(study, user, public = True)

    if the_interaction is not None:
        the_mooclet = MOOCletModel.find_mooclet({'_id': the_interaction['moocletId']})
        return (the_mooclet)
    else:
        root_mooclet = MOOCletModel.find_mooclet({"_id": study['rootMOOClet']})
        return inductive_get_mooclet(root_mooclet, user)

def assign_treatment(deployment_name, study_name, user, where = None, apiToken = None, other_information = None):

    deployment = DeploymentModel.get_one({'name': deployment_name}, public = True)
    if deployment is None:
        raise DeploymentNotFound(f"Deployment {deployment_name} not found or you don't have permission.")
    if deployment['apiToken'] != None and deployment['apiToken'] != apiToken:
        raise InvalidDeploymentToken(f"Invalid token for deployment {deployment_name}.")
    
    study = StudyModel.get_one({'deploymentId': ObjectId(deployment['_id']), 'name': study_name}, public = True)

    if study is None:
        raise StudyNotFound(f"Study {study_name} not found in {deployment_name}.")
    
    # check if the studyis stopped or not.
    if study['status'] == 'stopped':
        raise StudyStopped(f"Study {study_name} in {deployment_name} has stopped.")
    
    start_time = time.time()
    the_mooclet = get_mooclet_for_user(study, user)
    try:
        mooclet = create_mooclet_instance(user, the_mooclet)
        version_to_show = mooclet.choose_arm(user, where, other_information)
        if DEV_MODE:
            end_time = time.time()
            execution_time = end_time - start_time
            the_log = {
                "policy": the_mooclet['policy'],
                "execution_time": execution_time, 
                "threads": threading.active_count(), 
                "timestamp": datetime.datetime.now()
            }
            TreatmentLog.insert_one(the_log)
        return version_to_show
    except Exception as e:
        if DEV_MODE:
            the_log = {
                "policy": the_mooclet['policy'],
                "error": True,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "threads": threading.active_count(), 
                "timestamp": datetime.datetime.now()
            }
            TreatmentLog.insert_one(the_log)
        return None

def get_reward(deployment_name, study_name, user, value, where = None, apiToken = None,  other_information = None):
    # Get MOOClet!

    deployment = DeploymentModel.get_one({'name': deployment_name}, public = True)

    if deployment is None:
        raise DeploymentNotFound(f"Deployment {deployment_name} not found or you don't have permission.")
    if deployment['apiToken'] != None and deployment['apiToken'] != apiToken:
        raise InvalidDeploymentToken(f"Invalid token for deployment {deployment_name}.")
    study = StudyModel.get_one({'deploymentId': ObjectId(deployment['_id']), 'name': study_name}, public = True)
    if study is None:
        raise StudyNotFound(f"Study {study_name} not found in {deployment_name}.")
    
    # check if the studyis stopped or not.
    if study['status'] == 'stopped':
        raise StudyStopped(f"Study {study_name} in {deployment_name} has stopped.")
    start_time = time.time()
    the_mooclet = get_mooclet_for_user(study, user)

    mooclet = create_mooclet_instance(user, the_mooclet)
    response = mooclet.get_reward(user, value, where, other_information)

    if DEV_MODE:
        end_time = time.time()
        execution_time = end_time - start_time

        the_log = {
            "policy": the_mooclet['policy'],
            "execution_time": execution_time, 
            "threads": threading.active_count(), 
            "timestamp": datetime.datetime.now()
        }
        RewardLog.insert_one(the_log)
    return response



# https://security.stackexchange.com/questions/154462/why-cant-we-use-post-method-for-all-requests
# GET : does not change anything server side, multiple GET with same parameters should get same response - typically get an account value
# POST : can make changes server side, multiple POST with same parameters can lead to different results and responses - typically add an amount to an account
# PUT : can make changes server side, multiple PUT with same parameters should lead to same result and response - typically set an account value

@user_interaction_apis.route("/apis/treatment", methods=["POST"])
def get_treatment():
    # read request body.
    try:
        deployment = request.json['deployment'] if 'deployment' in request.json else None
        study = request.json['study'] if 'study' in request.json else None
        user = request.json['user'] if 'user' in request.json else None
        where = request.json['where'] if 'where' in request.json else None
        other_information = request.json['other_information'] if 'other_information' in request.json else None
        apiToken = request.json['apiToken'] if 'apiToken' in request.json else None

        if deployment is None or study is None or user is None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Please make sure deployment, study, user are provided."
            }), 400    
        else:        
            return json_util.dumps({
                "status_code": 200,
                "message": "This is your treatment.", 
                "treatment": assign_treatment(deployment, study, user, where, apiToken, other_information)
            }), 200
        
    except StudyNotFound as e:
        return json_util.dumps({
            "status_code": 404,
            "message": str(e)
        }), 404
    
    except DeploymentNotFound as e:
        return json_util.dumps({
            "status_code": 404,
            "message": str(e)
        }), 404
    
    except InvalidDeploymentToken as e:
        return json_util.dumps({
            "status_code": 401,
            "message": str(e)
        }), 401
    
    except StudyStopped as e:
        return json_util.dumps({
            "status_code": 409,
            "message": str(e)
        }), 409

    except Exception as e:
        return json_util.dumps({
            "status_code": 500,
            "message": "Server is down please try again later."
        }), 500
    


@user_interaction_apis.route("/apis/reward", methods=["POST"])
def give_reward():
    # read request body.
    try:
        deployment = request.json['deployment'] if 'deployment' in request.json else None
        study = request.json['study'] if 'study' in request.json else None
        user = request.json['user'] if 'user' in request.json else None
        where = request.json['where'] if 'where' in request.json else None
        other_information = request.json['other_information'] if 'other_information' in request.json else None
        value = request.json['value'] if 'value' in request.json else None
        apiToken = request.json['apiToken'] if 'apiToken' in request.json else None

        if deployment is None or study is None or user is None or value is None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Please make sure deployment, study, user and value are provided."
            }), 400
        else:        
            result = get_reward(deployment, study, user, value, where, apiToken, other_information)

        return json_util.dumps({
            "status_code": 200,
            "message": "Reward is saved."
        }), 200
            
    except OrphanReward as e:
        return json_util.dumps({
            "status_code": 400,
            "message": str(e)
        }), 400

    except StudyNotFound as e:
        return json_util.dumps({
            "status_code": 404,
            "message": str(e)
        }), 404
    
    except DeploymentNotFound as e:
        return json_util.dumps({
            "status_code": 404,
            "message": str(e)
        }), 404
    
    except InvalidDeploymentToken as e:
        return json_util.dumps({
            "status_code": 401,
            "message": str(e)
        }), 401
    
    except StudyStopped as e:
        return json_util.dumps({
            "status_code": 409,
            "message": str(e)
        }), 409

    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500,
            "message": "Server is down please try again later."
        }), 500



def give_variable_value(variableName, user, value, where = None, apiToken = None, other_information = None):
    current_time = datetime.datetime.now()
    the_variable = {
        "variableName": variableName,
        "user": user,
        "value": value,
        "where": where,
        "other_information": other_information,
        "timestamp": current_time
    }
    VariableValueModel.insert_variable_value(the_variable)
    return 200

@user_interaction_apis.route("/apis/variable", methods=["POST"])
def give_variable():
    # save a contextual varialble.
    try:
        deployment = request.json['deployment'] if 'deployment' in request.json else None
        study = request.json['study'] if 'study' in request.json else None
        variableName = request.json['variableName'] if 'variableName' in request.json else None
        user = request.json['user'] if 'user' in request.json else None
        value = request.json['value'] if 'value' in request.json else None
        where = request.json['where'] if 'where' in request.json else None
        other_information = request.json['other_information'] if 'other_information' in request.json else None
        apiToken = request.json['apiToken'] if 'apiToken' in request.json else None

        if deployment is None or study is None or variableName is None or user is None or value is None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Please make sure variableName, user, value are provided."
            }), 400


        the_deployment = DeploymentModel.get_one({"name": deployment}, public = True)

        if the_deployment is None:
            raise DeploymentNotFound(f"Deployment {deployment} not found or you don't have permission.")
        if the_deployment['apiToken'] != None and the_deployment['apiToken'] != apiToken:
            raise InvalidDeploymentToken(f"Invalid token for deployment {deployment}.")
        the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']}, public = True)
        if the_study is None:
            raise StudyNotFound(f"Study {study} not found or you don't have permission.")
        
        # check if the studyis stopped or not.
        if study['status'] == 'stopped':
            raise StudyStopped(f"Study {study} in {deployment} has stopped.")
        
        elif the_study['variables'] is None or variableName not in the_study['variables']:
            raise VariableNotInStudy(f"Variable {variableName} is not in study {study} in deployment {deployment}.")
        else:
            doc = VariableModel.get_one({"name": variableName}, public = True)
            if doc is None: raise VariableNotExist(f"Variable {variableName} does not exist.")
            give_variable_value(variableName, user, value, where, apiToken, other_information)

        return json_util.dumps({
                    "status_code": 200,
                    "message": "Variable value is saved."
                }), 200
    except StudyNotFound as e:
        return json_util.dumps({
            "status_code": 404,
            "message": str(e)
        }), 404
    except DeploymentNotFound as e:
        return json_util.dumps({
            "status_code": 404,
            "message": str(e)
        }), 404
    except InvalidDeploymentToken as e:
        return json_util.dumps({
            "status_code": 401,
            "message": str(e)
        }), 401
    except VariableNotExist as e:
        return json_util.dumps({
            "status_code": 404,
            "message": str(e)
        }), 404
    
    except VariableNotInStudy as e:
        return json_util.dumps({
            "status_code": 400,
            "message": str(e)
        }), 400
    
    except StudyStopped as e:
        return json_util.dumps({
            "status_code": 409,
            "message": str(e)
        }), 409
    except Exception as e:
        return json_util.dumps({
            "status_code": 500,
            "message": str(e)
        }), 500

