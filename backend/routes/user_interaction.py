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

user_interaction_apis = Blueprint('user_interaction_apis', __name__)

def create_assigner_instance(user, the_assigner):
    cls = globals().get(the_assigner['policy'])
    if cls:
        return cls(user, **the_assigner)
    else:
        raise ValueError(f"Invalid policy name")
    
def inductive_get_assigner(assigner, user):
    if len(assigner['children']) > 0:
        children = AssignerModel.find_assigners({"_id": {"$in": assigner['children']}}, {"_id": 1, "weight": 1})
        # TODO: Check previous assignment. Choose Assigner should be consistent with previous assignment.
        next_assigner_id = random_by_weight(list(children))['_id']
        next_assigner = AssignerModel.find_assigner({'_id': next_assigner_id})
        return inductive_get_assigner(next_assigner, user)
    else:
        # this is a leaf node. return it!
        return assigner

def get_assigner_for_user(study, user):
    # Note that, a deployment + study_name + user uniquely identify a assigner.
    # OR, this function will decide one and return.
    # TODO: Check if re-assignment is needed. For example, the assigner is deleted (not yet implemented), or the experiment requires re-assignment at a certain time point.
    # Find the latest interaction.
    the_interaction = InteractionModel.find_last_interaction(study, user, public = True)

    if the_interaction is not None:
        the_assigner = AssignerModel.find_assigner({'_id': the_interaction['assignerId']})
        return (the_assigner)
    else:
        root_assigner = AssignerModel.find_assigner({"_id": study['rootAssigner']})
        return inductive_get_assigner(root_assigner, user)

def assign_treatment(deployment_name, study_name, user, where = None, apiToken = None, other_information = None, request_different_arm = False):

    deployment = DeploymentModel.get_one({'name': deployment_name}, public = True)
    if deployment is None:
        raise DeploymentNotFound(f"Deployment {deployment_name} not found or you don't have permission.")
    if 'apiToken' in deployment != None and deployment['apiToken'] != apiToken:
        raise InvalidDeploymentToken(f"Invalid token for deployment {deployment_name}.")
    
    study = StudyModel.get_one({'deploymentId': ObjectId(deployment['_id']), 'name': study_name}, public = True)

    if study is None:
        raise StudyNotFound(f"Study {study_name} not found in {deployment_name}.")
    
    # check if the studyis stopped or not.
    if study['status'] == 'stopped':
        raise StudyStopped(f"Study {study_name} in {deployment_name} has stopped.")
    
    start_time = time.time()
    the_assigner = get_assigner_for_user(study, user)
    try:
        assigner = create_assigner_instance(user, the_assigner)
        version_to_show = assigner.choose_arm(user, where, other_information,request_different_arm)
        if DEV_MODE:
            end_time = time.time()
            execution_time = end_time - start_time
            the_log = {
                "policy": the_assigner['policy'],
                "execution_time": execution_time, 
                "threads": threading.active_count(), 
                "timestamp": datetime.datetime.now()
            }
            TreatmentLog.insert_one(the_log)
        return version_to_show
    except Exception as e:
        if DEV_MODE:
            the_log = {
                "policy": the_assigner['policy'],
                "error": True,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "threads": threading.active_count(), 
                "timestamp": datetime.datetime.now()
            }
            TreatmentLog.insert_one(the_log)
        return None

def get_reward(deployment_name, study_name, user, value, where = None, apiToken = None,  other_information = None):
    # Get Assigner!

    deployment = DeploymentModel.get_one({'name': deployment_name}, public = True)

    if deployment is None:
        raise DeploymentNotFound(f"Deployment {deployment_name} not found or you don't have permission.")
    if 'apiToken' in deployment and deployment['apiToken'] != apiToken:
        raise InvalidDeploymentToken(f"Invalid token for deployment {deployment_name}.")
    study = StudyModel.get_one({'deploymentId': ObjectId(deployment['_id']), 'name': study_name}, public = True)
    if study is None:
        raise StudyNotFound(f"Study {study_name} not found in {deployment_name}.")
    
    # check if the studyis stopped or not.
    if study['status'] == 'stopped':
        raise StudyStopped(f"Study {study_name} in {deployment_name} has stopped.")
    start_time = time.time()
    the_assigner = get_assigner_for_user(study, user)

    assigner = create_assigner_instance(user, the_assigner)
    response = assigner.get_reward(user, value, where, other_information)

    if DEV_MODE:
        end_time = time.time()
        execution_time = end_time - start_time

        the_log = {
            "policy": the_assigner['policy'],
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
        request_different_arm = request.json['requestDifferentArm'] if 'requestDifferentArm' in request.json else False

        if deployment is None or study is None or user is None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Please make sure deployment, study, user are provided."
            }), 400    
        else:        
            return json_util.dumps({
                "status_code": 200,
                "message": "This is your treatment.", 
                "treatment": assign_treatment(deployment, study, user, where, apiToken, other_information, request_different_arm)
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

    except NoDifferentTreatmentAvailable as e:
        return json_util.dumps({
            "status_code": 400,
            "message": str(e)
        }), 400

    except Exception as e:
        print(traceback.format_exc())
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
        value = float(request.json['value']) if 'value' in request.json else None
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
        print(traceback.format_exc())
        return json_util.dumps({
            "status_code": 500,
            "message": "Server is down please try again later."
        }), 500



def give_variable_value(deployment, variable, user, value, where = None, other_information = None):
    current_time = datetime.datetime.now()
    the_variable = {
        "deployment": deployment,
        "variable": variable,
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
        variable = request.json['variable'] if 'variable' in request.json else None
        user = request.json['user'] if 'user' in request.json else None
        value = request.json['value'] if 'value' in request.json else None
        where = request.json['where'] if 'where' in request.json else None
        other_information = request.json['other_information'] if 'other_information' in request.json else None
        apiToken = request.json['apiToken'] if 'apiToken' in request.json else None
        if deployment is None or variable is None or user is None or value is None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Please make sure deployment, variable, user, value are provided."
            }), 400


        the_deployment = DeploymentModel.get_one({"name": deployment}, public = True)

        if the_deployment is None:
            raise DeploymentNotFound(f"Deployment {deployment} not found or you don't have permission.")
        
        print(the_deployment)
        if 'apiToken' in the_deployment and the_deployment['apiToken'] != apiToken:
            raise InvalidDeploymentToken(f"Invalid token for deployment {deployment}.")

        doc = VariableModel.get_one({"name": variable}, public = True)
        if doc is None: raise VariableNotExist(f"Variable {variable} does not exist.")
        give_variable_value(deployment, variable, user, value, where, other_information)

        return json_util.dumps({
                    "status_code": 200,
                    "message": "Variable value is saved."
                }), 200
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
    except Exception as e:
        print(traceback.format_exc())
        return json_util.dumps({
            "status_code": 500,
            "message": str(e)
        }), 500

