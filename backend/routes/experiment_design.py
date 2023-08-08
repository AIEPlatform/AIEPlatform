from credentials import *
from flask import Blueprint, session
from flask import request
from bson import json_util
from bson.objectid import ObjectId
from helpers import *
import datetime
from Models.AssignerModel import AssignerModel
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
from routes.user_interaction import give_variable_value, assign_treatment, get_reward

from Policies.UniformRandom import UniformRandom
from Policies.ThompsonSamplingContextual import ThompsonSamplingContextual
from Policies.TSConfigurable import TSConfigurable
from Policies.WeightedRandom import WeightedRandom
from Policies.GPT import GPT


experiment_design_apis = Blueprint('experiment_design_apis', __name__)

def convert_front_list_assigners_into_tree(assigners):
    # Create a study for a deployment.

    # convert it into a tree.
    #TODO: tell us at least one assigner is needed.
    assigners.sort(key=lambda x: x['id'], reverse=False)
    nodes = {}

    # Step 2: Add each node to the dictionary
    for assigner in assigners:
        node_id = assigner["id"]
        nodes[node_id] = assigner

    # Step 3: Assign children to their respective parent nodes
    for assigner in assigners:
        parent_id = assigner["parent"]
        if parent_id != 0:
            parent_node = nodes[parent_id]
            if "children" not in parent_node:
                parent_node["children"] = []
            parent_node["children"].append(assigner)

    # Step 4: Retrieve the root node(s) of the tree
    root_nodes = None
    for assigner in assigners:
        if assigner["parent"] == 0:
            root_nodes = assigner
            break

    #TODO: Need to manually make a root assigner.

    def clean_assigner_object_helper(assigner):
        for key in ['id', 'parent', 'droppable', 'isOpen', 'text']:
            assigner.pop(key, None)
        if 'children' not in assigner:
            assigner['children'] = []
        if 'dbId' in assigner:
            assigner['_id'] = assigner['dbId']
            del assigner['dbId']
        for child in assigner['children']: 
            clean_assigner_object_helper(child)

    clean_assigner_object_helper(root_nodes)
    



    #TODO: Check if everythin is valid or not...

    return root_nodes


def create_assigner(assigner, study_id, session):
    time = datetime.datetime.now()
    my_children = []
    for child in assigner['children']:
        child_assigner_id = create_assigner(child, study_id, session)
        my_children.append(child_assigner_id)

    doc = AssignerModel.find_assigner({'name': assigner['name'], 'studyId': study_id})
    if doc is not None: return doc['_id'] #TODO: check if it's correct.

    new_assigner = {
        "name": assigner['name'],
        "policy": assigner['policy'],
        "parameters": assigner['parameters'],
        "studyId": study_id,
        "reassignAfterReward": assigner['reassignAfterReward'] if 'reassignAfterReward' in assigner else False,
        "autoZeroThreshold": assigner['autoZeroThreshold'] if 'autoZeroThreshold' in assigner else 0,
        "isConsistent": False, 
        "autoZeroPerMinute": False, 
        "children": my_children, 
        "weight": float(assigner['weight']), 
        "createdAt": time
    }

    response = AssignerModel.create(new_assigner, session=session)
    return response.inserted_id


def checkIfVersionsAreValid(versions):
    # check if any two versions have the same versionJSON.
    # check if any two versions have the same name.

    #version is a list of object with keys: name, versionJSON(which is a dict, like {factor1:0}).

    seen_names = {}

    # Iterate over the objects and check for duplicates
    for version in versions:
        if version['name'] in seen_names:
            raise DuplicatedVersionJSON('At least two versions have the exactly the same name.')
        else:
            seen_names[version['name']] = 1
        
    seen_version_jsons = {}

    for version in versions:
        if json.dumps(version['versionJSON']) in seen_version_jsons:
            raise DuplicatedVersionJSON('At least two versions have the exactly the same version json.')
        else:
            seen_version_jsons[json.dumps(version['versionJSON'])] = 1

    for i in range(len(versions)):
        for key, value in versions[i]['versionJSON'].items():
            try:
                number_value = float(value)  # Try to convert the value to a float
                versions[i]['versionJSON'][key] = number_value
            except ValueError:
                raise ValueError(f"Please make sure that every factor in the version json is a valid number.")

    return versions

    

# Create a study for a deployment.
# This function should be atomic. (TODO: testing it).
# This function should verify if the given study is valid or not. (TODO: keep completing it).
@experiment_design_apis.route("/apis/experimentDesign/study", methods=["POST"])
def create_study():

    if check_if_loggedin() == False:
        return json_util.dumps({
            "status_code": 401
        }), 401
    

    studyName = request.json['name'] if 'name' in request.json else None
    deploymentName = request.json['deployment'] if 'deployment' in request.json else None;
    assigners = [
        {
            "id": 1,
            "parent": 0,
            "droppable": True,
            "isOpen": True,
            "text": "assigner1",
            "name": "assigner1",
            "policy": "UniformRandom",
            "parameters": {},
            "weight": 1
        }
    ]
    versions = []
    factors = []
    variables = []
    rewardInformation = {
            "name": "reward",
            "min": 0,
            "max": 1
        }
    simulationSetting = {
            "baseReward": {},
            "contextualEffects": [],
            "numDays": 5
        }
    status = 'reset';

    with client.start_session() as session:
        session.start_transaction()
        try:
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

            assigner_trees = convert_front_list_assigners_into_tree(assigners)

            doc = StudyModel.get_one({'deploymentId': ObjectId(the_deployment['_id']), 'name': studyName}, public = True)
            if doc is not None: 
                return json_util.dumps({
                    "status_code": 400, 
                    "message": "Study name already exists."
                }), 400
            
            the_study = {
                'name': studyName,
                'deploymentId': the_deployment['_id'],
                'versions': versions,
                'variables': variables, 
                'factors': factors,
                'rewardInformation': rewardInformation, 
                'simulationSetting': simulationSetting,
                "status": status
            }
            # Induction to create assigner
            response = StudyModel.create(the_study, session=session)
            study_id = response.inserted_id
            root_assigner = create_assigner(assigner_trees, study_id, session=session)
            Study.update_one({'_id': study_id}, {'$set': {'rootAssigner': root_assigner}}, session=session)
            session.commit_transaction()

            studies = Study.find({"deploymentId": ObjectId(the_deployment['_id'])})
            the_study = Study.find_one({'_id': study_id})
            assigners = build_json_for_study(the_study['_id'])
            the_study['assigners'] = assigners # Note that in DB, we only save the root assigner!
            return json_util.dumps({
                "status_code": 200, 
                "message": "success", 
                "studies": studies,
                "theStudy": the_study
            }), 200
        
        except DuplicatedVersionJSON as e:
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 409,
                "message": str(e)
            }), 409
        
        except DuplicatedVersionName as e:
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 409,
                "message": str(e)
            }), 409
        
        except ValueError as e:
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 400,
                "message": str(e)
            }), 400
        except Exception as e:
            print(traceback.format_exc())
            session.abort_transaction()
            print("Transaction rolled back!")
            return json_util.dumps({
                "status_code": 500,
                "message": "Not successful, please try again later."
            }), 500


@experiment_design_apis.route("/apis/my_deployments", methods=["GET"])
def my_deployments():
    my_deployments = DeploymentModel.get_many({})
    return json_util.dumps({
        "status_code": 200,
        "message": "These are my deployments.",
        "my_deployments": my_deployments
    }), 200


@experiment_design_apis.route("/apis/experimentDesign/deployment", methods=["GET"])
def my_deployment():
    deployment_name = request.args.get('deployment_name') if 'deployment_name' in request.args else None
    if deployment_name is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please provide deployment_id or deployment_name."
        }), 400
    else:
        the_deployment = DeploymentModel.get_one({"name": deployment_name})
        if the_deployment is None:
            return json_util.dumps({
                "status_code": 403,
                "message": "You don't have access to this deployment. You will be redirected to the page where you can select your deployment."
            }), 403
        return json_util.dumps({
            "status_code": 200,
            "message": "This the deployment.",
            "deployment": the_deployment
        }), 200


@experiment_design_apis.route("/apis/experimentDesign/the_studies", methods=["GET"])
def the_studies():
    deployment_id = request.args.get('deployment_id') if 'deployment_id' in request.args else None
    if deployment_id is None:
        deployment_name = request.args.get('deployment_name') if 'deployment_name' in request.args else None
        if deployment_name is None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Please provide deployment_id or deployment_name."
            }), 400
        else:
            the_deployment = DeploymentModel.get_one({"name": deployment_name})
            if the_deployment is None:
                return json_util.dumps({
                    "status_code": 400,
                    "message": "Deployment does not exist."
                }), 400
            else:
                deployment_id = the_deployment['_id']
    studies = Study.find({"deploymentId": ObjectId(deployment_id)})
    return json_util.dumps({
        "status_code": 200,
        "message": "These are my studies.",
        "studies": studies
    }), 200



@experiment_design_apis.route("/apis/create_deployment", methods = ["POST"])
def create_deployment():
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
        

def convert_assigner_tree_to_list(assigner, parentId, assigner_list):
    the_id = len(assigner_list) + 1
    assigner_list.append({
        "id": the_id,
        "dbId": assigner["_id"], # we need this to update assigner.
        "parent": parentId,
        "droppable": True,
        "isOpen": True,
        "text": assigner["name"],
        "name": assigner["name"],
        "policy": assigner["policy"],
        "parameters": assigner["parameters"],
        "weight": assigner["weight"], 
        "isConsistent": assigner["isConsistent"] if "isConsistent" in assigner else None,
        "reassignAfterReward": assigner['reassignAfterReward'] if "reassignAfterReward" in assigner else None,
        "autoZeroPerMinute": assigner["autoZeroPerMinute"] if "autoZeroPerMinute" in assigner else None, 
        "autoZeroThreshold": assigner['autoZeroThreshold'] if 'autoZeroThreshold' in assigner else 0
    })
    for child in assigner["children"]:
        child_assigner = AssignerModel.find_assigner({"_id": child})
        convert_assigner_tree_to_list(child_assigner, the_id, assigner_list)


def build_json_for_study(studyId):
    the_study = StudyModel.get_one({"_id": studyId})
    the_root_assigner = AssignerModel.find_assigner({"_id": the_study["rootAssigner"]})
    assigner_list = []
    convert_assigner_tree_to_list(the_root_assigner, 0, assigner_list)
    return assigner_list

# TODO: Important: loading existing study.
@experiment_design_apis.route("/apis/experimentDesign/study", methods = ["GET"])
def load_existing_study():
    # load from params.
    deployment = request.args.get('deployment') # Name
    study = request.args.get('study') # Name
    the_deployment = DeploymentModel.get_one({"name": deployment})
    theStudy = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
    assigners = build_json_for_study(theStudy['_id'])
    theStudy['assigners'] = assigners # Note that in DB, we only save the root assigner!
    return json_util.dumps(
        {
        "status_code": 200,
        "study": theStudy
        }
    ), 200




def isExistingAssigner(assigner):
    return '_id' in assigner

def modify_assigner(assigner, study_id, session):
    # Modify or Create
    time = datetime.datetime.now()
    my_children = []
    for child in assigner['children']:
        child_assigner_id = modify_assigner(child, study_id, session)
        my_children.append(child_assigner_id)

    if isExistingAssigner(assigner):
        # update
        AssignerModel.update({'_id': ObjectId(assigner['_id']['$oid'])}, {
            "$set": {
                "name": assigner['name'],
                "policy": assigner['policy'],
                "parameters": assigner['parameters'],
                "studyId": study_id,
                "isConsistent": assigner['isConsistent'], 
                "reassignAfterReward": assigner['reassignAfterReward'] if "reassignAfterReward" in assigner else None,
                "autoZeroThreshold": assigner['autoZeroThreshold'] if 'autoZeroThreshold' in assigner else 0,
                "children": my_children, 
                "weight": float(assigner['weight']), 
                "updatedAt": time
            }
        }, session=session)
        return ObjectId(assigner['_id']['$oid'])
    else:
        new_assigner = {
            "name": assigner['name'],
            "policy": assigner['policy'],
            "parameters": assigner['parameters'],
            "studyId": study_id,
            "isConsistent": False, 
            "reassignAfterReward": assigner['reassignAfterReward'] if "reassignAfterReward" in assigner else None,
            "autoZeroThreshold": assigner['autoZeroThreshold'] if 'autoZeroThreshold' in assigner else 0,
            "autoZeroPerMinute": False, 
            "children": my_children, 
            "weight": float(assigner['weight']), 
            "createdAt": time, 
            "updatedAt": time
        }
        response = AssignerModel.create(new_assigner, session=session)
        return response.inserted_id
    
def checkIfAssignersAreValid(assigners):
    # TODO: Need different cases, need to call static functions of each class.

    for i in range(len(assigners)):
        cls = globals().get(assigners[i]['policy'])
        assigners[i] = cls.validate_assigner(assigners[i])

    return assigners

@experiment_design_apis.route("/apis/experimentDesign/study", methods = ["PUT"])
def modify_existing_study():
    # load from request body.
    deployment = 'deployment' in request.json and request.json['deployment'] or None # Name
    study = 'study' in request.json and request.json['study'] or None # Name

    if deployment is None or study is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure the deployment, study, assigners, versions, variables are provided."
        }), 400

    with client.start_session() as session:
        try:
            session.start_transaction()

            
            # TODO: check if the following exists (it's part of validate)
            assigners = study['assigners']
            versions = study['versions']
            variables = study['variables']
            factors = study['factors']
            studyName = study['name']
            status = study['status'] if 'status' in study else 'stopped'

            the_deployment = DeploymentModel.get_one({"name": deployment})
            the_study = StudyModel.get_one({"name": studyName, "deploymentId": the_deployment['_id']})

            versions = checkIfVersionsAreValid(versions)
            assigners = checkIfAssignersAreValid(assigners)

            

            Study.update_one({'_id': the_study['_id']}, {'$set': {
                'versions': versions, 
                'variables': variables,
                'factors': factors,
                'status': status
                }}, session=session)
            
            # get all assigners of this study. Remove assigners whose _id are not present in the assigners list.

            assigners_in_db = AssignerModel.find_assigners({"studyId": the_study['_id']})

            assigners_id_to_keep = [ObjectId(assigner['dbId']['$oid']) for assigner in assigners if 'dbId' in assigner]

            assigners_id_to_remove = []

            for assigner_in_db in list(assigners_in_db):
                if assigner_in_db['_id'] not in assigners_id_to_keep:
                    assigners_id_to_remove.append(assigner_in_db['_id'])

            Assigner.delete_many({"_id": {"$in": assigners_id_to_remove}}, session=session)

            designer_tree = convert_front_list_assigners_into_tree(assigners)

            modify_assigner(designer_tree, the_study['_id'], session=session)

            session.commit_transaction()

        except DuplicatedVersionJSON as e:
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 409,
                "message": str(e)
            }), 409
        
        except DuplicatedVersionName as e:
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 409,
                "message": str(e)
            }), 409
        except ValueError as e:
            session.abort_transaction()
            return json_util.dumps({
                "status_code": 400,
                "message": str(e)
            }), 400
        except Exception as e:
            print(traceback.format_exc())
            session.abort_transaction()
            print("Transaction rolled back!")
            return json_util.dumps({
                "status_code": 500,
                "message": "Not successful, please try again later."
            }), 500
        
    study = StudyModel.get_one({"name": studyName, "deploymentId": the_deployment['_id']})
    return json_util.dumps(
        {
        "status_code": 200,
        "message": "Study is modified.", 
        "temp": designer_tree,
        "study": study
        }
    ), 200

@experiment_design_apis.route("/apis/variables", methods=["GET"])
def get_variables():
    # get showStudies from params if not, set to False.
    showStudies = request.args.get('showStudies') == 'true' if 'showStudies' in request.args else False
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    try:
        variables = list(VariableModel.get_many({}))
        if showStudies:
            # for every variables, get the studies that use it. Every study has a list called variables.
            for variable in variables:
                studies = list(StudyModel.get_many({"variables": { "$elemMatch": { "$eq": variable['name'] } }}, showDeploymentName = True))
                # get deploymentName for each study by deployment Id.
                variable['studies'] = [f'{study["name"]} in {study["deployment"]["name"]}' for study in studies]

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

@experiment_design_apis.route("/apis/experimentDesign/variable", methods=["POST"])
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

        # update the status to reset.
        Study.update_one({'_id': studyId}, {'$set': {
            'status': 'reset'
            }}, session=session)
        # get all assigner ids
        assigners = AssignerModel.find_assigners({"studyId": ObjectId(studyId)})
        assignerids = [assigner['_id'] for assigner in assigners]
        # reset all assigner parameters to the earliest one in the History collection.
        for assignerId in assignerids:
            # get the earliest history by timestamp
            history_parameter = History.find_one({"assignerId": ObjectId(assignerId)}, sort=[("timestamp", pymongo.ASCENDING)], session=session)
            if history_parameter is not None:
                # update the assigner
                AssignerModel.update_policy_parameters(ObjectId(assignerId),  {"parameters": history_parameter['parameters']}, session=session)
                # remove all history
                History.delete_many({"assignerId": ObjectId(assignerId)}, session=session)
            # Remove all interactions.
            Interaction.delete_many({"assignerId": ObjectId(assignerId)}, session=session)
            # remove individualLevel history
            AssignerIndividualLevelInformation.delete_many({"assignerId": ObjectId(assignerId)}, session=session)
            DatasetModel.delete_study_datasets(the_deployment, the_study)
        return 200
    except Exception as e:
        print(traceback.format_exc())
        return 500


@experiment_design_apis.route("/apis/experimentDesign/changeStudyStatus", methods=["PUT"])
def reset_study():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    deployment = request.json['deployment'] if 'deployment' in request.json else None
    study = request.json['study'] if 'study' in request.json else None
    status = request.json['status'] if 'status' in request.json else None
    if deployment is None or study is None or status is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please provide deployment, study and status."
        }), 400
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
        try:
            session.start_transaction()
            if status == "reset":
                response = reset_study_helper(the_deployment, the_study, session)
                if response == 200:
                    session.commit_transaction()
                    return json_util.dumps({
                        "status_code": 200,
                        "message": "Done."
                    }), 200
                else:
                    session.abort_transaction()
                    return json_util.dumps({
                        "status_code": 500,
                        "message": "Something went wrong, please try again later."
                    }), 500
            else:
                # update study status
                # if new status is running, check if simulation is running. If so, return 400.

                if status == "running":
                    # check if simulation is running
                    if 'simulationStatus' in the_study and the_study['simulationStatus'] == "running":
                        return json_util.dumps({
                            "status_code": 400,
                            "message": "The simulation is running. Please stop it first."
                        }), 400
                Study.update_one({'_id': the_study['_id']}, {'$set': {
                    'status': status
                    }}, session=session)
                
                session.commit_transaction()
                return json_util.dumps({
                    "status_code": 200,
                    "message": "Done."
                }), 200
        except Exception as e:

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
            AssignerModel.delete_study_assigners(the_study['_id'], session=session)
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
from Models.InteractionModel import InteractionModel
requestSession = requests.Session()
@experiment_design_apis.route("/apis/experimentDesign/runSimulation", methods=["POST"])
def run_simulation():
    # TODO: before allowing a simulation to be started, check if there is sufficient threads available.

    def fake_data_time(deployment, study, numDays=5):
        numDays = int(numDays)
        the_deployment = DeploymentModel.get_one({"name": deployment})
        the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
        assignerids = list(
            Assigner.find({"studyId": the_study['_id']}).distinct("_id")
        )
        the_interactions = list(InteractionModel.get_many({"assignerId": {"$in": assignerids}}, public=True).sort("timestamp", pymongo.ASCENDING))
        # change the rewardTimestamp this way:
        # first 20% of the interactions, change the rewardTimestamp to four days ago.
        # second 20% of the interactions, change the rewardTimestamp to three days ago.
        # third 20% of the interactions, change the rewardTimestamp to two days ago.
        # fourth 20% of the interactions, change the rewardTimestamp to one day ago.
        # fifth 20% of the interactions, change the rewardTimestamp: no change.

        # create an array of 10 arrays
        time_assigner_lists = [[] for i in range(numDays)]
        
        for i in range(0, len(the_interactions)):
            if the_interactions[i]['rewardTimestamp'] is None: continue

            for day in range(numDays):
                if i < 1/numDays * day * len(list(the_interactions)):
                    time_assigner_lists[day].append(the_interactions[i]['_id'])
                    break


        for i in range(0, len(time_assigner_lists)):
            Interaction.update_many({"_id": {"$in": time_assigner_lists[i]}}, {"$set": {"rewardTimestamp": datetime.datetime.now() - datetime.timedelta(days=i)}})
    def compare_values(a, b):
        return (float(a) - float(b)) == 0

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
        # check if study is running. If so, don't run simulation.
        if 'status' in the_study and the_study['status'] == 'running': #TODO: didn't test this because the simulation option is hidden from frontend when a study is running.
            return json_util.dumps({
                "status_code": 400,
                "message": "The study is running. Please stop the study first."
            }), 400
        Study.update_one({'_id': the_study['_id']}, {'$set': {
            'simulationSetting': simulationSetting
            }})
    except Exception as e:
        return json_util.dumps({
            "status_code": 404, 
            "message": "Can't find the study."
        }), 404
    

    apiToken = the_deployment['apiToken'] if 'apiToken' in the_deployment else None
    

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
                give_variable_value(deployment, variable, user, predictor, where = 'simulation', fromSimulation = True)
            version_to_show = assign_treatment(deployment, study, user, where = 'simulation', apiToken = apiToken, other_information = None, request_different_arm = False, fromSimulation = True)
            treatment = version_to_show['name']
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
                                break                            
            if random.random() < rewardProb:
                value = 1
            else:
                value = 0
            get_reward(deployment, study, user, value, where = 'simulation', apiToken = apiToken,  other_information = None, fromSimulation=True)
        fake_data_time(deployment, study, simulationSetting['numDays'])

        print("Simulation Done")
        # change simulationStatus back to idle.
        Study.update_one({"_id": the_study['_id']}, {"$set": {"simulationStatus": "idle"}})
    except Exception as e:
        print(traceback.format_exc())
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
    

import random
import string
# generate deployment api token.
@experiment_design_apis.route('/apis/experimentDesign/generateDeploymentApiToken', methods=['PUT'])
def generate_deployment_api_token():
    def generate_token(length=32):
        # Define the characters that can be used in the token
        characters = string.ascii_letters + string.digits

        # Generate a random token using the specified length
        token = ''.join(random.choice(characters) for _ in range(length))

        return token

    deployment = request.json['deployment'] if 'deployment' in request.json else None
    if deployment is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please provide deployment name."
        }), 400
    try:
        the_deployment = DeploymentModel.get_one({"name": deployment})
        token = generate_token(32) 
        Deployment.update_one({"_id": the_deployment['_id']}, {"$set": {"apiToken": token}})
        my_deployments = DeploymentModel.get_many({})
        the_deployment = DeploymentModel.get_one({"name": deployment})
        return json_util.dumps({
            "status_code": 200,
            "deployments": my_deployments, 
            "theDeployment": the_deployment
        }), 200
    except Exception as e:
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500
    


@experiment_design_apis.route('/apis/experimentDesign/deleteDeploymentApiToken', methods=['PUT'])
def delete_deployment_api_token():

    deployment = request.json['deployment'] if 'deployment' in request.json else None
    if deployment is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please provide deployment name."
        }), 400
    try:
        the_deployment = DeploymentModel.get_one({"name": deployment})
        Deployment.update_one({"_id": the_deployment['_id']}, {"$set": {"apiToken": None}})
        my_deployments = DeploymentModel.get_many({})
        the_deployment = DeploymentModel.get_one({"name": deployment})
        return json_util.dumps({
            "status_code": 200,
            "deployments": my_deployments, 
            "theDeployment": the_deployment
        }), 200
    except Exception as e:
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500