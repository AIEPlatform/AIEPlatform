from credentials import *
from flask import Blueprint, session
from flask import request
from bson import json_util
from bson.objectid import ObjectId
from helpers import *
import datetime
from Models.MOOCletModel import MOOCletModel
from Models.StudyModel import StudyModel
from Models.DeploymentModel import DeploymentModel
from Models.DatasetModel import DatasetModel
from Models.VariableModel import VariableModel
from Models.InteractionModel import InteractionModel
from errors import *
import pandas as pd
from bson.objectid import ObjectId
from flask import send_file, make_response
from Analysis.basic_reward_summary_table import basic_reward_summary_table
from Analysis.AverageRewardByTime import AverageRewardByTime


integration_apis = Blueprint('integration_apis', __name__)

# This has APIs the developers of other apps can use to integrate DataArrow into their apps.
# First example is the Pilot Study that happened in 2023-07.

# TODO: we need to merge this file with user_interaction.py. Also, we need to make some sort of API tokens.
@integration_apis.route('/apis/integration/findUserInteractions', methods=['GET'])
def find_user_interactions():
    # load from params.
    deployment = request.args.get('deployment')
    study = request.args.get('study')
    user = request.args.get('user')
    # if where in params, then use it. Otherwise, use None.
    where = request.args.get('where') 

    if deployment is None or study is None or user is None:
        return json_util.dumps({
            "status_code": 400, 
            "message": "deployment, study, and user must be provided."
        })
    
    # find the deployment object.
    deployment_object = DeploymentModel.get_one({"name": deployment}, public = True)

    if deployment_object is None:
        return json_util.dumps({
            "status_code": 404, 
            "message": "deployment not found"
        })
    # find the study object.
    study_object = StudyModel.get_one({"name": study, "deploymentId": deployment_object['_id']}, public = True)
    if study_object is None:
        return json_util.dumps({
            "status_code": 404, 
            "message": "study not found"
        })
    
    # get all mooclet ids in the study.
    moocletIds = MOOCletModel.find_study_mooclets(study_object, public = True)
    moocletIds = [moocletId['_id'] for moocletId in moocletIds]
    # find the interactions
    filter = {
        "moocletId": {"$in": moocletIds},
        "user": user
    }

    if where is not None:
        filter['where'] = where

    # find if any interaction has outcome not nan;
    interactions = InteractionModel.get_many(filter, public = True)
    return json_util.dumps({
        "status_code": 200,
        "interactions": interactions
    })
