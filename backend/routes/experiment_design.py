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
    time = datetime.datetime.utcnow()
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
        "isConsistent": False, 
        "autoZeroPerMinute": False, 
        "children": my_children, 
        "weight": float(mooclet['weight']), 
        "createdAt": time
    }

    response = MOOCletModel.create(new_mooclet, session=session)
    return response.inserted_id

@experiment_design_apis.route("/apis/study", methods=["POST"])
def create_study():
    if check_if_loggedin() == False:
        return json_util.dumps({
            "status_code": 401
        }), 401
    
    study_name = request.json['studyName']
    mooclets = request.json['mooclets']
    versions = request.json['versions']
    variables = request.json['variables']
    factors = request.json['factors']
    deploymentName = request.json['deploymentName']
    rewardInformation = request.json['rewardInformation']

    the_deployment = DeploymentModel.get_one({'name': deploymentName})

    # TODO: Check if the deployment exists or not.
    if the_deployment is None:
        return json_util.dumps({
            "status_code": 400, 
            "message": "Deployment does not exist or you don't have access."
        }), 400

    mooclet_trees = convert_front_list_mooclets_into_tree(mooclets)

    doc = StudyModel.get_one({'deploymentId': ObjectId(the_deployment['_id']), 'name': study_name}, public = True)
    if doc is not None: 
        return json_util.dumps({
            "status_code": 400, 
            "message": "Study name already exists."
        }), 400

    with client.start_session() as session:
        try:
            session.start_transaction()
            the_study = {
                'name': study_name,
                'deploymentId': the_deployment['_id'],
                'versions': versions,
                'variables': variables, 
                'factors': factors,
                'rewardInformation': rewardInformation
            }
            # Induction to create mooclet
            response = StudyModel.create(the_study, session=session)
            study_id = response.inserted_id
            root_mooclet = create_mooclet(mooclet_trees, study_id, session=session)
            Study.update_one({'_id': study_id}, {'$set': {'rootMOOClet': root_mooclet}}, session=session)
            session.commit_transaction()
        except Exception as e:
            print(e)
            session.abort_transaction()
            print("Transaction rolled back!")
            return json_util.dumps({
                "status": 500,
                "message": "Not successful, please try again later."
            }), 500

    return json_util.dumps({
        "status": 200, 
        "message": "success"
    }), 200


@experiment_design_apis.route("/apis/my_deployments", methods=["GET"])
def my_deployments():
    user = "chenpan"
    my_deployments = DeploymentModel.get_many({"collaborators": {"$in": [user]}})
    return json_util.dumps({
        "status_code": 200,
        "message": "These are my deployments.",
        "my_deployments": my_deployments
    }), 200


@experiment_design_apis.route("/apis/the_studies", methods=["GET"])
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
@experiment_design_apis.route("/apis/load_existing_study", methods = ["GET"])
def load_existing_study():
    # load from params.
    deployment = request.args.get('deployment') # Name
    study = request.args.get('study') # Name
    the_deployment = DeploymentModel.get_one({"name": deployment})
    the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
    studyName = the_study['name'] # Note that we don't allow study name to be changed.
    variables = the_study['variables']
    versions = the_study['versions']
    factors = the_study['factors']
    rewardInformation = the_study['rewardInformation'] if 'rewardInformation' in the_study else {"name": "reward", "min": 0, "max": 1}
    mooclets = build_json_for_study(the_study['_id'])
    return json_util.dumps(
        {
        "status_code": 200,
        "studyName": studyName,
        "variables": variables,
        "versions": versions, 
        "factors": factors,
        "mooclets": mooclets,
        "rewardInformation": rewardInformation
        }
    ), 200




def isExistingMOOClet(mooclet):
    return '_id' in mooclet

def modify_mooclet(mooclet, study_id, session):
    # Modify or Create
    print(mooclet)
    time = datetime.datetime.utcnow()
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
                "autoZeroPerMinute": False, 
                "children": my_children, 
                "weight": float(mooclet['weight']), 
                "modifiedAt": time
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
            "autoZeroPerMinute": False, 
            "children": my_children, 
            "weight": float(mooclet['weight']), 
            "createdAt": time
        }
        response = MOOCletModel.create(new_mooclet, session=session)
        return response.inserted_id

@experiment_design_apis.route("/apis/modify_existing_study", methods = ["PUT"])
def modify_existing_study():
    # load from request body.
    deployment = 'deployment' in request.json and request.json['deployment'] or None # Name
    study = 'study' in request.json and request.json['study'] or None # Name
    mooclets = request.json['mooclets']
    versions = request.json['versions']
    variables = request.json['variables']

    if deployment is None or study is None or mooclets is None or versions is None or variables is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure the deployment, study, mooclets, versions, variables are provided."
        }), 400
    
    the_deployment = DeploymentModel.get_one({"name": deployment})
    the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})

    with client.start_session() as session:
        try:
            session.start_transaction()
            Study.update_one({'_id': the_study['_id']}, {'$set': {
                'versions': versions, 
                'variables': variables
                }}, session=session)
            

            designer_tree = convert_front_list_mooclets_into_tree(mooclets)

            print(designer_tree)
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

        # check if the variable name exists
        doc = VariableModel.get_one({"name": new_variable_name}, public = True)
        if doc is not None:
            return json_util.dumps({
                "status_code": 400, 
                "message": "The variable name exists."
            }), 400
        VariableModel.create({
            "name": new_variable_name,
            "min": new_variable_min,
            "max": new_variable_max,
            "type": new_variable_type,
            "owner": username, 
            "collaborators": [], 
            "created_at": datetime.datetime.now()
        })

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
    




@experiment_design_apis.route("/apis/experimentDesign/resetStudy", methods=["PUT"])
def reset_study():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    studyId = request.json['studyId']
    with client.start_session() as session:
        try:
            session.start_transaction()
            # get all mooclet ids
            mooclets = MOOCletModel.find_mooclets({"studyId": ObjectId(studyId)})
            mooclet_ids = [mooclet['_id'] for mooclet in mooclets]
            # reset all mooclet parameters to the earliest one in the History collection.
            for mooclet_id in mooclet_ids:
                # get the earliest history by timestamp
                print(mooclet_id)
                history_parameter = History.find_one({"moocletId": ObjectId(mooclet_id)}, sort=[("timestamp", pymongo.ASCENDING)], session=session)
                # update the mooclet
                if history_parameter is None: continue
                MOOCletModel.update_policy_parameters(ObjectId(mooclet_id),  {"parameters": history_parameter['parameters']}, session=session)
                # remove all history
                History.delete_many({"moocletId": ObjectId(mooclet_id)}, session=session)
                # Remove all interactions.
                Interaction.delete_many({"moocletId": ObjectId(mooclet_id)}, session=session)
                # remove individualLevel history
                MOOCletIndividualLevelInformation.delete_many({"moocletId": ObjectId(mooclet_id)}, session=session)
            session.commit_transaction()

            return json_util.dumps({
                "status_code": 200,
                "message": "The study has been reset."
            }), 200

        except Exception as e:
            print(e)
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 500, 
                "message": e
            }), 500