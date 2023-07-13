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
from errors import *
import pandas as pd
from bson.objectid import ObjectId
from flask import send_file, make_response
from Analysis.basic_reward_summary_table import basic_reward_summary_table
from Analysis.AverageRewardByTime import AverageRewardByTime


experiment_design_apis = Blueprint('experiment_design_apis', __name__)

def convert_front_list_mooclets_into_tree(mooclets):
    # Create a study for a deployment.

    # convert it into a tree.
    #TODO: tell us at least one mooclet is needed.
    mooclets.sort(key=lambda x: x['id'], reverse=False)
    nodes = {}

    # Step 2: Add each node to the dictionary
    for mooclet in mooclets:
        node_id = mooclet["id"]
        nodes[node_id] = mooclet

    # Step 3: Assign children to their respective parent nodes
    for mooclet in mooclets:
        parent_id = mooclet["parent"]
        if parent_id != 0:
            parent_node = nodes[parent_id]
            if "children" not in parent_node:
                parent_node["children"] = []
            parent_node["children"].append(mooclet)

    # Step 4: Retrieve the root node(s) of the tree
    root_nodes = None
    for mooclet in mooclets:
        if mooclet["parent"] == 0:
            root_nodes = mooclet
            break

    #TODO: Need to manually make a root mooclet.

    def clean_mooclet_object_helper(mooclet):
        for key in ['id', 'parent', 'droppable', 'isOpen', 'text']:
            mooclet.pop(key, None)
        if 'children' not in mooclet:
            mooclet['children'] = []
        if 'dbId' in mooclet:
            mooclet['_id'] = mooclet['dbId']
            del mooclet['dbId']
        for child in mooclet['children']: 
            clean_mooclet_object_helper(child)

    clean_mooclet_object_helper(root_nodes)
    



    #TODO: Check if everythin is valid or not...

    return root_nodes


def create_mooclet(mooclet, study_id, session):
    time = datetime.datetime.now()
    my_children = []
    for child in mooclet['children']:
        child_mooclet_id = create_mooclet(child, study_id, session)
        my_children.append(child_mooclet_id)

    doc = MOOCletModel.find_mooclet({'name': mooclet['name'], 'studyId': study_id})
    if doc is not None: return doc['_id'] #TODO: check if it's correct.

    new_mooclet = {
        "name": mooclet['name'],
        "policy": mooclet['policy'],
        "parameters": mooclet['parameters'],
        "studyId": study_id,
        "reassignAfterReward": mooclet['reassignAfterReward'] if 'reassignAfterReward' in mooclet else False,
        "isConsistent": False, 
        "autoZeroPerMinute": False, 
        "children": my_children, 
        "weight": float(mooclet['weight']), 
        "createdAt": time
    }

    response = MOOCletModel.create(new_mooclet, session=session)
    return response.inserted_id

# Create a study for a deployment.
# This function should be atomic. (TODO: testing it).
# This function should verify if the given study is valid or not. (TODO: keep completing it).
@experiment_design_apis.route("/apis/experimentDesign/study", methods=["POST"])
def create_study():

    if check_if_loggedin() == False:
        return json_util.dumps({
            "status_code": 401
        }), 401
    
    study = request.json['study'] if 'study' in request.json else None;

    if study is None:
        return json_util.dumps({
            "status_code": 400, 
            "message": "Missing required parameters."
        }), 400
    

    studyName = study['name'] if 'name' in study else None;
    mooclets = study['mooclets'] if 'mooclets' in study else None;
    versions = study['versions'] if 'versions' in study else None;
    variables = study['variables'] if 'variables' in study else None;
    factors = study['factors'] if 'factors' in study else None;
    rewardInformation = study['rewardInformation'] if 'rewardInformation' in study else None;
    simulationSetting = study['simulationSetting'] if 'simulationSetting' in study else None;

    deploymentName = request.json['deploymentName'] if 'deploymentName' in request.json else None;
    

    # TODO: Check if valid study name or not.
    if len(studyName) < 3 or len(studyName) > 50:
        return json_util.dumps({
            "status_code": 400, 
            "message": "Study name should be between 3 and 50 characters."
        }), 400


    the_deployment = DeploymentModel.get_one({'name': deploymentName});

    # TODO: Check if the deployment exists or not.
    if the_deployment is None:
        return json_util.dumps({
            "status_code": 400, 
            "message": "Deployment does not exist or you don't have access."
        }), 400

    mooclet_trees = convert_front_list_mooclets_into_tree(mooclets)

    doc = StudyModel.get_one({'deploymentId': ObjectId(the_deployment['_id']), 'name': studyName}, public = True)
    if doc is not None: 
        return json_util.dumps({
            "status_code": 400, 
            "message": "Study name already exists."
        }), 400

    with client.start_session() as session:
        try:
            session.start_transaction()
            the_study = {
                'name': studyName,
                'deploymentId': the_deployment['_id'],
                'versions': versions,
                'variables': variables, 
                'factors': factors,
                'rewardInformation': rewardInformation, 
                'simulationSetting': simulationSetting
            }
            # Induction to create mooclet
            response = StudyModel.create(the_study, session=session)
            study_id = response.inserted_id
            root_mooclet = create_mooclet(mooclet_trees, study_id, session=session)
            Study.update_one({'_id': study_id}, {'$set': {'rootMOOClet': root_mooclet}}, session=session)
            session.commit_transaction()

            studies = Study.find({"deploymentId": ObjectId(the_deployment['_id'])})
            the_study = Study.find_one({'_id': study_id})
            return json_util.dumps({
                "status_code": 200, 
                "message": "success", 
                "studies": studies,
                "study": the_study
            }), 200
        except Exception as e:
            print(e)
            session.abort_transaction()
            print("Transaction rolled back!")
            return json_util.dumps({
                "status_code": 500,
                "message": "Not successful, please try again later."
            }), 500


@experiment_design_apis.route("/apis/my_deployments", methods=["GET"])
def my_deployments():
    user = "chenpan"
    my_deployments = DeploymentModel.get_many({"collaborators": {"$in": [user]}})
    return json_util.dumps({
        "status_code": 200,
        "message": "These are my deployments.",
        "my_deployments": my_deployments
    }), 200


@experiment_design_apis.route("/apis/experimentDesign/the_studies", methods=["GET"])
def the_studies():
    deployment_id = request.args.get('deployment_id')
    studies = Study.find({"deploymentId": ObjectId(deployment_id)})
    return json_util.dumps({
        "status_code": 200,
        "message": "These are my studies.",
        "studies": studies
    }), 200



@experiment_design_apis.route("/apis/create_deployment", methods = ["POST"])
def create_deployment():
    user = "chenpan"
    name = request.json['name'] if 'name' in request.json else None
    description = request.json['description'] if 'description' in request.json else None
    collaborators = request.json['collaborators'] if 'collaborators' in request.json else None
    if name is None or description is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure deployment_name, deployment_studies are provided."
        }), 400
    else:
        the_Deployment = DeploymentModel.get_one({"name": name}, public = True)
        if the_Deployment is not None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Deployment name is already used."
            }), 400
        else:
            DeploymentModel.create({
                "name": name,
                "description": description,
                "collaborators": collaborators,
            })
            return json_util.dumps({
                "status_code": 200,
                "message": "Deployment is created."
            }), 200
        

def convert_mooclet_tree_to_list(mooclet, parentId, mooclet_list):
    the_id = len(mooclet_list) + 1
    mooclet_list.append({
        "id": the_id,
        "dbId": mooclet["_id"], # we need this to update mooclet.
        "parent": parentId,
        "droppable": True,
        "isOpen": True,
        "text": mooclet["name"],
        "name": mooclet["name"],
        "policy": mooclet["policy"],
        "parameters": mooclet["parameters"],
        "weight": mooclet["weight"], 
        "isConsistent": mooclet["isConsistent"] if "isConsistent" in mooclet else None,
        "reassignAfterReward": mooclet['reassignAfterReward'] if "reassignAfterReward" in mooclet else None,
        "autoZeroPerMinute": mooclet["autoZeroPerMinute"] if "autoZeroPerMinute" in mooclet else None
    })
    for child in mooclet["children"]:
        child_mooclet = MOOCletModel.find_mooclet({"_id": child})
        convert_mooclet_tree_to_list(child_mooclet, the_id, mooclet_list)


def build_json_for_study(studyId):
    the_study = StudyModel.get_one({"_id": studyId})
    the_root_mooclet = MOOCletModel.find_mooclet({"_id": the_study["rootMOOClet"]})
    mooclet_list = []
    convert_mooclet_tree_to_list(the_root_mooclet, 0, mooclet_list)
    return mooclet_list

# TODO: Important: loading existing study.
@experiment_design_apis.route("/apis/experimentDesign/study", methods = ["GET"])
def load_existing_study():
    # load from params.
    deployment = request.args.get('deployment') # Name
    study = request.args.get('study') # Name
    the_deployment = DeploymentModel.get_one({"name": deployment})
    theStudy = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
    mooclets = build_json_for_study(theStudy['_id'])
    theStudy['mooclets'] = mooclets # Note that in DB, we only save the root mooclet!
    return json_util.dumps(
        {
        "status_code": 200,
        "study": theStudy
        }
    ), 200




def isExistingMOOClet(mooclet):
    return '_id' in mooclet

def modify_mooclet(mooclet, study_id, session):
    # Modify or Create
    time = datetime.datetime.now()
    my_children = []
    for child in mooclet['children']:
        child_mooclet_id = modify_mooclet(child, study_id, session)
        my_children.append(child_mooclet_id)

    if isExistingMOOClet(mooclet):
        # update
        MOOCletModel.update({'_id': ObjectId(mooclet['_id']['$oid'])}, {
            "$set": {
                "name": mooclet['name'],
                "policy": mooclet['policy'],
                "parameters": mooclet['parameters'],
                "studyId": study_id,
                "isConsistent": False, 
                "reassignAfterReward": mooclet['reassignAfterReward'] if "reassignAfterReward" in mooclet else None,
                "autoZeroPerMinute": False, 
                "children": my_children, 
                "weight": float(mooclet['weight']), 
                "updatedAt": time
            }
        }, session=session)
        return ObjectId(mooclet['_id']['$oid'])
    else:
        new_mooclet = {
            "name": mooclet['name'],
            "policy": mooclet['policy'],
            "parameters": mooclet['parameters'],
            "studyId": study_id,
            "isConsistent": False, 
            "reassignAfterReward": mooclet['reassignAfterReward'] if "reassignAfterReward" in mooclet else None,
            "autoZeroPerMinute": False, 
            "children": my_children, 
            "weight": float(mooclet['weight']), 
            "createdAt": time, 
            "updatedAt": time
        }
        response = MOOCletModel.create(new_mooclet, session=session)
        return response.inserted_id

@experiment_design_apis.route("/apis/experimentDesign/study", methods = ["PUT"])
def modify_existing_study():
    # load from request body.
    deployment = 'deployment' in request.json and request.json['deployment'] or None # Name
    study = 'study' in request.json and request.json['study'] or None # Name

    if deployment is None or study is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure the deployment, study, mooclets, versions, variables are provided."
        }), 400

    # TODO: check if the following exists (it's part of validate)
    mooclets = study['mooclets']
    versions = study['versions']
    variables = study['variables']
    studyName = study['name']

    the_deployment = DeploymentModel.get_one({"name": deployment})
    the_study = StudyModel.get_one({"name": studyName, "deploymentId": the_deployment['_id']})

    with client.start_session() as session:
        try:
            session.start_transaction()
            Study.update_one({'_id': the_study['_id']}, {'$set': {
                'versions': versions, 
                'variables': variables
                }}, session=session)
            

            designer_tree = convert_front_list_mooclets_into_tree(mooclets)

            modify_mooclet(designer_tree, the_study['_id'], session=session)

            session.commit_transaction()
        except Exception as e:
            print(e)
            session.abort_transaction()
            print("Transaction rolled back!")
            return json_util.dumps({
                "status_code": 500,
                "message": "Not successful, please try again later."
            }), 500
    return json_util.dumps(
        {
        "status_code": 200,
        "message": "Study is modified.", 
        "temp": designer_tree
        }
    ), 200

@experiment_design_apis.route("/apis/variables", methods=["GET"])
def get_variables():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    try:
        variables = VariableModel.get_many({})
        return json_util.dumps({
            "status_code": 200, 
            "data": variables
        }), 200
    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500

@experiment_design_apis.route("/apis/variable", methods=["POST"])
def create_variable():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    try:
        username = get_username()

        data = request.get_json()
        new_variable_name = data['newVariableName']
        new_variable_min = data['newVariableMin']
        new_variable_max = data['newVariableMax']
        new_variable_type = data['newVariableType']
        new_variable_value_prompt = 'variableValuePromptL' in data and data['variableValuePromptL'] or ""


        # check if the variable name exists
        doc = VariableModel.get_one({"name": new_variable_name}, public = True)
        if doc is not None:
            return json_util.dumps({
                "status_code": 400, 
                "message": "The variable name exists."
            }), 400
        
        newVariable = {
            "name": new_variable_name,
            "min": new_variable_min,
            "max": new_variable_max,
            "type": new_variable_type,
            "owner": username, 
            "collaborators": [], 
            "created_at": datetime.datetime.now()
        }
        if new_variable_type == "text":
            newVariable['variableValuePrompt'] = new_variable_value_prompt
        VariableModel.create(newVariable)

        return json_util.dumps({
            "status_code": 200,
            "message": "The variable is created successfully."
        }), 200

    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500
    

def reset_study_helper(the_deployment, the_study, session):
    try:
        studyId = the_study['_id']
        # get all mooclet ids
        mooclets = MOOCletModel.find_mooclets({"studyId": ObjectId(studyId)})
        mooclet_ids = [mooclet['_id'] for mooclet in mooclets]
        # reset all mooclet parameters to the earliest one in the History collection.
        for mooclet_id in mooclet_ids:
            # get the earliest history by timestamp
            history_parameter = History.find_one({"moocletId": ObjectId(mooclet_id)}, sort=[("timestamp", pymongo.ASCENDING)], session=session)
            if history_parameter is not None:
                # update the mooclet
                MOOCletModel.update_policy_parameters(ObjectId(mooclet_id),  {"parameters": history_parameter['parameters']}, session=session)
                # remove all history
                History.delete_many({"moocletId": ObjectId(mooclet_id)}, session=session)
            # Remove all interactions.
            Interaction.delete_many({"moocletId": ObjectId(mooclet_id)}, session=session)
            # remove individualLevel history
            MOOCletIndividualLevelInformation.delete_many({"moocletId": ObjectId(mooclet_id)}, session=session)
            DatasetModel.delete_study_datasets(the_deployment, the_study)
        return 200
    except Exception as e:
        print(traceback.format_exc())
        return 500


@experiment_design_apis.route("/apis/experimentDesign/resetStudy", methods=["PUT"])
def reset_study():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    deployment = request.json['deployment']
    study = request.json['study']
    the_deployment = DeploymentModel.get_one({"name": deployment})
    if the_deployment is None: 
        return json_util.dumps({
            "status_code": 403,
            "message": "You don't have access to the study."
        }), 403
    the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
    if the_study is None: 
        return json_util.dumps({
            "status_code": 403,
            "message": "You don't have access to the study."
        }), 403
    with client.start_session() as session:
        session.start_transaction()
        response = reset_study_helper(the_deployment, the_study, session)
        if response == 200:
            session.commit_transaction()
            return json_util.dumps({
                "status_code": 200,
                "message": "The study is reset successfully."
            }), 200
        else:
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 500,
                "message": "Something went wrong, please try again later."
            }), 500
    

import traceback
# well, 
def delete_study_helper(the_deployment, the_study, session):
    try:
        resetResponse = reset_study_helper(the_deployment, the_study, session)
        if resetResponse != 200:
            return resetResponse
        else:
            # delete the study
            StudyModel.delete_one_by_id(the_study['_id'], session=session)
            MOOCletModel.delete_study_mooclets(the_study['_id'], session=session)
            return 200
    except Exception as e:
        print(traceback.format_exc())
        return 500
    

@experiment_design_apis.route("/apis/experimentDesign/study", methods=["DELETE"])
def delete_study():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    deployment = request.json['deployment']
    study = request.json['study']
    the_deployment = DeploymentModel.get_one({"name": deployment})
    if the_deployment is None: 
        return json_util.dumps({
            "status_code": 403,
            "message": "You don't have access to the study."
        }), 403
    the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
    if the_study is None: 
        return json_util.dumps({
            "status_code": 403,
            "message": "You don't have access to the study."
        }), 403
    with client.start_session() as session:
        session.start_transaction()
        response = delete_study_helper(the_deployment, the_study, session)
        if response == 200:
            session.commit_transaction()
            return json_util.dumps({
                "status_code": 200,
                "message": "The study is deleted successfully."
            }), 200
        elif response == 403:
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 403,
                "message": "You don't have access to the study."
            }), 403
        else:
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 500,
                "message": "Something went wrong, please try again later."
            }), 500
        


@experiment_design_apis.route("/apis/experimentDesign/deployment", methods=["DELETE"])
def delete_deployment():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    deployment = request.json['deployment']
    the_deployment = DeploymentModel.get_one({"name": deployment})
    if the_deployment is None: 
        return json_util.dumps({
            "status_code": 403,
            "message": "You don't have access to the deployment."
        }), 403
    with client.start_session() as session:
        try:
            session.start_transaction()
            # get all studies
            studies = StudyModel.get_deployment_studies(the_deployment['_id'])
            for study in studies:
                if delete_study_helper(the_deployment, study, session) != 200:
                    # throw an error
                    session.abort_transaction()
                    return json_util.dumps({
                        "status_code": 500,
                        "message": "Something went wrong, please try again later."
                    }), 500

            # delete the deployment
            DeploymentModel.delete_one_by_id(the_deployment['_id'], session=session)
            session.commit_transaction()
            return json_util.dumps({
                "status_code": 200,
                "message": "The deployment is deleted successfully."
            }), 200
        except Exception as e:
            print(traceback.format_exc())
            session.abort_transaction()
            
            return json_util.dumps({
                "status_code": 500,
                "message": "Something went wrong, please try again later."
            }), 500


@experiment_design_apis.route("/apis/experimentDesign/updateSimulationSetting", methods=["PUT"])
# read deployment and study name from the request body.
def update_simulation_setting():
    deployment = request.json['deployment'] if 'deployment' in request.json else None
    study = request.json['study'] if 'study' in request.json else None
    simulationSetting = request.json['simulationSetting'] if 'simulationSetting' in request.json else None
    if deployment is None or study is None or simulationSetting is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please provide deployment and study name and simulationSetting."
        }), 400
    try:
        # get study object. But get deployment object first.
        the_deployment = DeploymentModel.get_one({"name": deployment})
        the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
        # update the the study object's simulation setting.
        Study.update_one({'_id': the_study['_id']}, {'$set': {
            'simulationSetting': simulationSetting
            }})
        return json_util.dumps({
            "status_code": 200,
            "message": "The simulation setting is updated."
        }), 200
    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500
    

# get simulationSetting
@experiment_design_apis.route("/apis/experimentDesign/getSimulationSetting", methods=["GET"])
def get_simulation_setting():
    deployment = request.args.get('deployment') # Name
    study = request.args.get('study') # Name
    if deployment is None or study is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please provide deployment and study name."
        }), 400
    try:
        the_deployment = DeploymentModel.get_one({"name": deployment})
        the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
        simulationSetting = the_study['simulationSetting'] if 'simulationSetting' in the_study else None

        if simulationSetting is None:
            return json_util.dumps({
                "status_code": 404,
                "message": "The simulation setting is not found."
            }), 404
        return json_util.dumps({
            "status_code": 200,
            "simulationSetting": simulationSetting
        }), 200
    except Exception as e:
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500
    
import json
import requests
import threading
from Models.InteractionModel import InteractionModel
requestSession = requests.Session()
@experiment_design_apis.route("/apis/experimentDesign/runSimulation", methods=["POST"])
def run_simulation():
    # TODO: before allowing a simulation to be started, check if there is sufficient threads available.

    def fake_data_time(deployment, study, numDays=5):
        numDays = int(numDays)
        the_deployment = DeploymentModel.get_one({"name": deployment})
        the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
        mooclet_ids = list(
            MOOClet.find({"studyId": the_study['_id']}).distinct("_id")
        )
        the_interactions = list(InteractionModel.get_many({"moocletId": {"$in": mooclet_ids}}, public=True).sort("timestamp", pymongo.ASCENDING))
        # change the rewardTimestamp this way:
        # first 20% of the interactions, change the rewardTimestamp to four days ago.
        # second 20% of the interactions, change the rewardTimestamp to three days ago.
        # third 20% of the interactions, change the rewardTimestamp to two days ago.
        # fourth 20% of the interactions, change the rewardTimestamp to one day ago.
        # fifth 20% of the interactions, change the rewardTimestamp: no change.

        # create an array of 10 arrays
        time_mooclet_lists = [[] for i in range(numDays)]
        
        for i in range(0, len(the_interactions)):
            if the_interactions[i]['rewardTimestamp'] is None: continue

            for day in range(numDays):
                if i < 1/numDays * day * len(list(the_interactions)):
                    time_mooclet_lists[day].append(the_interactions[i]['_id'])
                    break


        for i in range(0, len(time_mooclet_lists)):
            Interaction.update_many({"_id": {"$in": time_mooclet_lists[i]}}, {"$set": {"rewardTimestamp": datetime.datetime.now() - datetime.timedelta(days=i)}})
    def compare_values(a, b):
        return (float(a) - float(b)) == 0
    def give_variable_value_helper(deployment, study, variableName, user, value):
        url = f'http://localhost:20110/apis/give_variable'
        headers = {'Content-Type': 'application/json'}
        payload = {'deployment': deployment, 'study': study, 'user': user, 'value': value, 'variableName': variableName, 'where': 'simulation'}
        response = requestSession.post(url, headers=headers, data=json.dumps(payload))
        return response
    
    def assign_treatment_helper(deployment, study, user):
        url = f'http://localhost:20110/apis/get_treatment'
        headers = {'Content-Type': 'application/json'}
        payload = {'deployment': deployment, 'study': study, 'user': user, 'where': 'simulation'}
        response = requestSession.post(url, headers=headers, data=json.dumps(payload))
        return response


    def get_reward_helper(deployment, study, user, value):
        url = f'http://localhost:20110/apis/give_reward'
        headers = {'Content-Type': 'application/json'}
        payload = {'deployment': deployment, 'study': study, 'user': user, 'value': value, 'where': 'simulation'}
        response = requestSession.post(url, headers=headers, data=json.dumps(payload))
        return response
    deployment = request.json['deployment'] if 'deployment' in request.json else None
    study = request.json['study'] if 'study' in request.json else None
    sampleSize = int(request.json['sampleSize']) if 'sampleSize' in request.json else None
    simulationSetting = request.json['simulationSetting'] if 'simulationSetting' in request.json else None
    

    
    if deployment is None or study is None or sampleSize is None or simulationSetting is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please provide deployment and study name and sample size and simulation setting."
        }), 400


    sampleSize = min([sampleSize, 1000])
    try:
        the_deployment = DeploymentModel.get_one({"name": deployment})
        the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
        Study.update_one({'_id': the_study['_id']}, {'$set': {
            'simulationSetting': simulationSetting
            }})
    except Exception as e:
        return json_util.dumps({
            "status_code": 404, 
            "message": "Can't find the study."
        }), 404
    

    # check if a simulation is running.
    if 'simulationStatus' in the_study and the_study['simulationStatus'] != 'idle':
        return json_util.dumps({
            "status_code": 400,
            "message": "The simulation is already running or stopping."
        }), 400

    # set simulationStatus to running.
    Study.update_one({"_id": the_study['_id']}, {"$set": {"simulationStatus": "running"}})

    try:
        for i in range(0, sampleSize):
            # check if simulationStatus has been changed to stopping or not.
            study_doc = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
            if 'simulationStatus' in study_doc and study_doc['simulationStatus'] == 'stopping':
                break
            user = f'{deployment}_{study}_simulated_user_{i}'
            variable_values = {}
            for variable in the_study['variables']:
                predictor = random.choice([0, 1])
                variable_values[variable] = predictor
                give_variable_value_helper(deployment, study, variable, user, predictor)
            assignResponse = assign_treatment_helper(deployment, study, user)
            treatment = assignResponse.json()['treatment']['name']
            rewardProb = 0.5
            # TODO: improve the efficiency of the following code.
            if treatment in simulationSetting['baseReward']:
                rewardProb = float(simulationSetting['baseReward'][treatment]) 
            
            # modify the reward prob based on the variable values.
            for variable in variable_values:
                for contextualEffect in simulationSetting['contextualEffects']:
                    if contextualEffect['variable'] == variable and contextualEffect['version'] == treatment:
                        if contextualEffect['operator'] == '=':
                            if compare_values(variable_values[variable], contextualEffect['value']):
                                rewardProb = rewardProb + float(contextualEffect['effect'])
                                print(rewardProb)
                                break                            
            if random.random() < rewardProb:
                value = 1
            else:
                value = 0
            get_reward_helper(deployment, study, user, value)
        fake_data_time(deployment, study, simulationSetting['numDays'])

        print("Simulation Done")
        # change simulationStatus back to idle.
        Study.update_one({"_id": the_study['_id']}, {"$set": {"simulationStatus": "idle"}})
    except Exception as e:
        Study.update_one({"_id": the_study['_id']}, {"$set": {"simulationStatus": "idle"}})



    return json_util.dumps({
        "status_code": 200,
        "message": "The simulation is running."
    }), 200



# stop a simulation
@experiment_design_apis.route('/apis/experimentDesign/stopSimulation', methods=['PUT'])
def stop_simulation():
    deployment = request.json['deployment'] if 'deployment' in request.json else None
    study = request.json['study'] if 'study' in request.json else None
    if deployment is None or study is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please provide deployment and study name."
        }), 400
    try:
        the_deployment = DeploymentModel.get_one({"name": deployment})
        the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})

        # update simulationStatus to stopping
        if the_study['simulationStatus'] == 'idle':
            return json_util.dumps({
                "status_code": 400,
                "message": "The simulation is not running."
            }), 400
        Study.update_one({"_id": the_study['_id']}, {"$set": {"simulationStatus": "stopping"}})
        return json_util.dumps({
            "status_code": 200
        }), 200
    except Exception as e:
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500