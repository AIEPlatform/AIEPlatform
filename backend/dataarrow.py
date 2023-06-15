from credentials import *
from flask import Blueprint, session
from flask import request
from bson import json_util
from bson.objectid import ObjectId
from helpers import *
from Policies.UniformRandom import UniformRandom
from Policies.ThompsonSamplingContextual import ThompsonSamplingContextual
import datetime
import time
import threading
from Models.VariableValueModel import VariableValueModel
from Models.InteractionModel import InteractionModel
from Models.MOOCletModel import MOOCletModel
from Models.StudyModel import StudyModel
from Models.DeploymentModel import DeploymentModel
from Models.DatasetModel import DatasetModel
from Models.VariableModel import VariableModel


dataarrow_apis = Blueprint('dataarrow_apis', __name__)
		
def create_mooclet_instance(the_mooclet):
    cls = globals().get(the_mooclet['policy'])
    if cls:
        return cls(**the_mooclet)
    else:
        raise ValueError(f"Invalid policy name")

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

@dataarrow_apis.route("/apis/study", methods=["POST"])
def create_study():
    if check_if_loggedin() == False:
        return json_util.dumps({
            "status_code": 401
        }), 401
    
    study_name = request.json['studyName']
    mooclets = request.json['mooclets']
    versions = request.json['versions']
    variables = request.json['variables']
    deploymentName = request.json['deploymentName']
    rewardInformation = request.json['rewardInformation']

    the_deployment = DeploymentModel.get_one({'name': deploymentName})

    # TODO: Check if the deployment exists or not.

    mooclet_trees = convert_front_list_mooclets_into_tree(mooclets)

    doc = StudyModel.get_one({'deploymentId': ObjectId(the_deployment['_id']), 'name': study_name})
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
                "status_code": 500,
                "message": "Not successful, please try again later."
            }), 500

    return json_util.dumps({
        "status_code": 200, 
        "message": "success"
    }), 200


def inductive_get_mooclet(mooclet, user):
    if len(mooclet['children']) > 0:
        children = MOOCletModel.find_mooclet({"_id": {"$in": mooclet['children']}}, {"_id": 1, "weight": 1})

        # TODO: Check previous assignment. Choose MOOClet should be consistent with previous assignment.
        next_mooclet_id = random_by_weight(list(children))['_id']
        next_mooclet = MOOCletModel.find_mooclet({'_id': next_mooclet_id})
        return inductive_get_mooclet(next_mooclet, user)
    else:
        # this is a leaf node. return it!
        return mooclet

def get_mooclet_for_user(deployment_name, study_name, user):
    # Note that, a deployment + study_name + user uniquely identify a mooclet.
    # OR, this function will decide one and return.
    deployment = DeploymentModel.get_one({'name': deployment_name})
    study = StudyModel.get_one({'deploymentId': ObjectId(deployment['_id']), 'name': study_name})
    # TODO: Check if re-assignment is needed. For example, the mooclet is deleted (not yet implemented), or the experiment requires re-assignment at a certain time point.


    # Find the latest interaction.
    the_interaction = InteractionModel.find_last_interaction(study, user)

    if the_interaction is not None:
        the_mooclet = MOOCletModel.find_mooclet({'_id': the_interaction['moocletId']})
        return (the_mooclet)
    else:
        root_mooclet = MOOCletModel.find_mooclet({"_id": study['rootMOOClet']})
        return inductive_get_mooclet(root_mooclet, user)

import traceback

def assign_treatment(deployment_name, study_name, user, where = None, other_information = None):
    start_time = time.time()
    the_mooclet = get_mooclet_for_user(deployment_name, study_name, user)
    try:
        mooclet = create_mooclet_instance(the_mooclet)
        version_to_show = mooclet.choose_arm(user, where, other_information)

        print(version_to_show)
        if DEBUG:
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
        if DEBUG:
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

def get_reward(deployment_name, study_name, user, value, where = None, other_information = None):
    # Get MOOClet!
    try:
        start_time = time.time()
        the_mooclet = get_mooclet_for_user(deployment_name, study_name, user)
        mooclet = create_mooclet_instance(the_mooclet)
        response = mooclet.get_reward(user, value, where, other_information)

        if DEBUG:
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
    except Exception as e:
        if DEBUG:
            the_log = {
                "policy": the_mooclet['policy'],
                "error": True, 
                "threads": threading.active_count(), 
                "timestamp": datetime.datetime.now()
            }
            RewardLog.insert_one(the_log)



# https://security.stackexchange.com/questions/154462/why-cant-we-use-post-method-for-all-requests
# GET : does not change anything server side, multiple GET with same parameters should get same response - typically get an account value
# POST : can make changes server side, multiple POST with same parameters can lead to different results and responses - typically add an amount to an account
# PUT : can make changes server side, multiple PUT with same parameters should lead to same result and response - typically set an account value

@dataarrow_apis.route("/apis/get_treatment", methods=["POST"])
def get_treatment():
    # read request body.
    try:
        start_time = time.time()
        deployment = request.json['deployment'] if 'deployment' in request.json else None
        study = request.json['study'] if 'study' in request.json else None
        user = request.json['user'] if 'user' in request.json else None
        where = request.json['where'] if 'where' in request.json else None
        other_information = request.json['other_information'] if 'other_information' in request.json else None

        if deployment is None or study is None or user is None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Please make sure deployment, study, user are provided."
            }), 400    
        else:        
            return json_util.dumps({
                "status_code": 200,
                "message": "This is your treatment.", 
                "treatment": assign_treatment(deployment, study, user, where, other_information)
            }), 200


    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500,
            "message": "Server is down please try again later."
        }), 500
    


@dataarrow_apis.route("/apis/give_reward", methods=["POST"])
def give_reward():
    # read request body.
    try:
        start_time = time.time()
        deployment = request.json['deployment'] if 'deployment' in request.json else None
        study = request.json['study'] if 'study' in request.json else None
        user = request.json['user'] if 'user' in request.json else None
        where = request.json['where'] if 'where' in request.json else None
        other_information = request.json['other_information'] if 'other_information' in request.json else None
        value = request.json['value'] if 'value' in request.json else None

        if deployment is None or study is None or user is None or value is None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Please make sure deployment, study, user are provided."
            }), 400    
        else:        
            result = get_reward(deployment, study, user, value, where, other_information)
            if result != 200:
                return json_util.dumps({
                    "status_code": 400,
                    "message": "No reward is saved."
                }), 400
            else:

                return json_util.dumps({
                    "status_code": 200,
                    "message": "Reward is saved."
                }), 200


    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500,
            "message": "Server is down please try again later."
        }), 500



def give_variable_value(deployment, study, variableName, user, value, where = None, other_information = None):

    the_deployment = DeploymentModel.get_one({"name": deployment})
    the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id'], "variables": {"$elemMatch": {"name": variableName}}})

    if the_study is None:
        return 400
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

@dataarrow_apis.route("/apis/give_variable", methods=["POST"])
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

        if deployment is None or study is None or variableName is None or user is None or value is None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Please make sure variableName, user, value are provided."
            }), 400
        else:
            doc = VariableModel.get_one({"name": variableName})
            if doc is None:
                return json_util.dumps({
                    "status_code": 400,
                    "message": "Variable is not found."
                }), 400
        

            
            give_variable_value(deployment, study, variableName, user, value, where, other_information)
            return json_util.dumps({
                "status_code": 200,
                "message": "Variable is saved."
            }), 200
    except Exception as e:
        print("Error in giving_variable:")
        print(e)
        return json_util.dumps({
            "status_code": 500,
            "message": "Server is down please try again later."
        }), 500



@dataarrow_apis.route("/apis/my_deployments", methods=["GET"])
def my_deployments():
    user = "chenpan"
    my_deployments = DeploymentModel.get_many({"collaborators": {"$in": [user]}})
    return json_util.dumps({
        "status_code": 200,
        "message": "These are my deployments.",
        "my_deployments": my_deployments
    }), 200


@dataarrow_apis.route("/apis/the_studies", methods=["GET"])
def the_studies():
    user = "chenpan"
    deployment_id = request.args.get('deployment_id')
    studies = Study.find({"deploymentId": ObjectId(deployment_id)})
    return json_util.dumps({
        "status_code": 200,
        "message": "These are my studies.",
        "studies": studies
    }), 200



@dataarrow_apis.route("/apis/create_deployment", methods = ["POST"])
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
        the_Deployment = DeploymentModel.get_one({"name": name})
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
        


# {"studyName":"sim","description":"test2 description","mooclets":[{"id":1,"parent":0,"droppable":true,"isOpen":true,"text":"mooclet1","name":"mooclet1","policy":"ThompsonSamplingContextual","parameters":{"batch_size":1,"variance_a":1,"variance_b":5,"uniform_threshold":1,"precision_draw":1,"updatedPerMinute":0,"include_intercept":true,"coef_cov":[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],"coef_mean":[0,0,0,0],"regressionFormulaItems":[[{"name":"test","index":0}],[{"name":"version1","content":"v1"}],[{"name":"test","index":0},{"name":"version1","content":"v1"}]]},"weight":100}],"variables":[{"name":"test","index":0}],"versions":[{"name":"version1","content":"v1"},{"name":"version2","content":"v2"}]}

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

# build_json_for_study(ObjectId("647a661c7c9b18cd1e4312d6"))



import pandas as pd
from flatten_json import flatten

def create_df_from_mongo(study_name, deployment_name):
    the_deployment = DeploymentModel.get_one({"name": deployment_name})
    the_study = StudyModel.get_one({"name": study_name, "deploymentId": the_deployment['_id']})

    result = InteractionModel.get_interactions(the_study)

    list_cur = list(result)
    df = pd.DataFrame(list_cur)

    if 'contextuals' in df.columns:
        df_normalized = pd.json_normalize(df['contextuals'].apply(flatten, args = (".",)))
        # Concatenate the flattened DataFrame with the original DataFrame
        df = pd.concat([df.drop('contextuals', axis=1), df_normalized], axis=1)

    df = df.rename(columns={
        "treatment$timestamp": "treatment.timestamp", 
        "outcome$timestamp": "outcome.timestamp"
        })
    

    column_names_without_dot_values = [c.replace(".value", "") for c in df.columns]

    print(column_names_without_dot_values)
    column_mapping = dict(zip(df.columns, column_names_without_dot_values))

    # Rename the columns
    df = df.rename(columns=column_mapping)
        

    return df


import pickle
import smtplib
from email.mime.text import MIMEText

@dataarrow_apis.route("/apis/create_dataset", methods = ["POST"])
def create_dataset():
    deployment = request.json['deployment'] if 'deployment' in request.json else None
    study = request.json['study'] if 'study' in request.json else None
    email = request.json['email'] if 'email' in request.json else None
    dataset_name = request.json['datasetName'] if 'datasetName' in request.json else None
    if deployment is None or study is None or email is None or dataset_name is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure deployment, study, email are provided."
        }), 400
    else:
        try:
            df = create_df_from_mongo(study, deployment)

            the_deployment = DeploymentModel.get_one({"name": deployment})
            the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})

            possible_variables = [v['name'] for v in the_study['variables']]


            variables = [v for v in list(df.columns) if v in possible_variables]


            binary_data = pickle.dumps(df)
            # TODO: Check if name is already used
            document = {
                'dataset': binary_data,
                'deployment': deployment, 
                'name': dataset_name,
                'study': study, 
                'variables': variables,
                'deploymentId': DeploymentModel.get_one({"name": deployment})['_id'],
                'createdAt': datetime.datetime.utcnow()
            }
            response = DatasetModel.create(document)

            subject = "Your MOOClets datasets are ready for download."
            body = f'Your MOOClets datasets are ready for download. Please visit this link: {ROOT_URL}/apis/analysis/downloadArrowDataset/{str(response.inserted_id)}'
            sender = EMAIL_USERNAME
            recipients = [request.get_json()['email']]
            password = EMAIL_PASSWORD
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipients, msg.as_string())

            return json_util.dumps({
                "status_code": 200,
                "message": "Dataset is created."
            }), 200
        except Exception as e:
            print(e)
            subject = "Sorry, downloading mooclet datasets failed. please try again."
            body = f'Sorry, downloading mooclet datasets failed. please try again.'
            sender = EMAIL_USERNAME
            recipients = [request.get_json()['email']]
            password = EMAIL_PASSWORD
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(sender, password)
                smtp_server.sendmail(sender, recipients, msg.as_string())
            return json_util.dumps({
                "status_code": 500, 
                "message": "Sorry, downloading mooclet datasets failed. please try again."
            }), 500
        


from bson.objectid import ObjectId
from flask import send_file, make_response

@dataarrow_apis.route("/apis/analysis/downloadArrowDataset/<id>", methods=["GET"])
def downloadArrowDataset(id):
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403 
    
    try:
        dataset = DatasetModel.get_one({"_id": ObjectId(id)})

        df = pickle.loads(dataset['dataset'])
        csv_string = df.to_csv(index=False)

        # Create a Flask response object with the CSV data
        response = make_response(csv_string)

        # Set the headers to tell the browser to download the file as a CSV
        response.headers['Content-Disposition'] = f'attachment; filename={dataset["name"]}_{dataset["createdAt"]}.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
    except:
        return json_util.dumps({
            "status_code": 500, 
            "message": "downloading error"
        }), 500
    


@dataarrow_apis.route("/apis/analysis/get_deployment_datasets", methods=["GET"])
def get_deployment_datasets():
    # load from params.
    deployment = request.args.get('deployment')
    the_deployment = DeploymentModel.get_one({"name": deployment})
    the_datasets = DatasetModel.get_many({"deploymentId": the_deployment['_id']}, {'dataset': 0})

    return json_util.dumps(
        {
        "status_code": 200,
        "datasets": the_datasets
        }
    ), 200
        

from Analysis.basic_reward_summary_table import basic_reward_summary_table

@dataarrow_apis.route("/apis/analysis/basic_reward_summary_table", methods = ["POST"])
def basic_reward_summary_table_api():
    theDatasetId = request.json['theDatasetId'] if 'theDatasetId' in request.json else None # This is the id.
    
    selected_variables = request.json['selectedVariables'] if 'selectedVariables' in request.json else None
 
    if theDatasetId is None or selected_variables is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure the_study_basic_info, selected_variables are provided."
        }), 400
    else:
        df = getDataset(theDatasetId)
        result_df = basic_reward_summary_table(df, selected_variables)
        return json_util.dumps({
            "status_code": 200,
            "message": "Table returned.",
            "result": {
                "columns": list(result_df.columns), 
                "rows": [tuple(r) for r in result_df.to_numpy()]
            }
        }), 200
    


from Analysis.AverageRewardByTime import AverageRewardByTime

@dataarrow_apis.route("/apis/analysis/AverageRewardByTime", methods = ["POST"])
def AverageRewardByTime_api():
    theDatasetId = request.json['theDatasetId'] if 'theDatasetId' in request.json else None # This is the id.
    
 
    if theDatasetId is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure the_study_basic_info, selected_variables are provided."
        }), 400
    else:
        df = getDataset(theDatasetId)
        result_df, groups = AverageRewardByTime(df, [])
        return json_util.dumps({
            "status_code": 200,
            "message": "Table returned.",
            "data": result_df, 
            "groups": groups
        }), 200
    


# TODO: Important: loading existing study.
@dataarrow_apis.route("/apis/load_existing_study", methods = ["GET"])
def load_existing_study():
    # load from params.
    deployment = request.args.get('deployment') # Name
    study = request.args.get('study') # Name
    the_deployment = DeploymentModel.get_one({"name": deployment})
    the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})
    studyName = the_study['name'] # Note that we don't allow study name to be changed.
    variables = the_study['variables']
    versions = the_study['versions']
    rewardInformation = the_study['rewardInformation'] if 'rewardInformation' in the_study else {"name": "reward", "min": 0, "max": 1}
    mooclets = build_json_for_study(the_study['_id'])
    return json_util.dumps(
        {
        "status_code": 200,
        "studyName": studyName,
        "variables": variables,
        "versions": versions, 
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

@dataarrow_apis.route("/apis/modify_existing_study", methods = ["PUT"])
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


@dataarrow_apis.route("/apis/variables", methods=["GET"])
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
    

@dataarrow_apis.route("/apis/variable", methods=["POST"])
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
        doc = VariableModel.get_one({"name": new_variable_name})
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