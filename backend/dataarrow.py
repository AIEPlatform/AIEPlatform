from credentials import *
from flask import Blueprint, session
from flask import request
from bson import json_util
from bson.objectid import ObjectId
import random
from helpers import *
from Policies.UniformRandom import UniformRandom
from Policies.ThompsonSamplingContextual import ThompsonSamplingContextual
import datetime
import time
import threading
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

    doc = MOOClet.find_one({'name': mooclet['name'], 'studyId': study_id})
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

    response = MOOClet.insert_one(new_mooclet, session=session)
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

    deploymentId = '6470c7ae9c36a48e2d5149cb'

    mooclet_trees = convert_front_list_mooclets_into_tree(mooclets)

    doc = Study.find_one({'deploymentId': ObjectId(deploymentId), 'name': study_name})
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
                'deploymentId': ObjectId(deploymentId),
                'versions': versions,
                'variables': variables
            }
            # Induction to create mooclet
            response = Study.insert_one(the_study, session=session)
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
        children = MOOClet.find({"_id": {"$in": mooclet['children']}}, {"_id": 1, "weight": 1})

        # TODO: Check previous assignment. Choose MOOClet should be consistent with previous assignment.
        next_mooclet_id = random_by_weight(list(children))['_id']
        next_mooclet = MOOClet.find_one({'_id': next_mooclet_id})
        return inductive_get_mooclet(next_mooclet, user)
    else:
        # this is a leaf node. return it!
        return mooclet

def get_mooclet_for_user(deployment_name, study_name, user):
    # Note that, a deployment + study_name + user uniquely identify a mooclet.
    # OR, this function will decide one and return.
    deployment = Deployment.find_one({'name': deployment_name})
    study = Study.find_one({'deploymentId': ObjectId(deployment['_id']), 'name': study_name})
    # TODO: Check if re-assignment is needed. For example, the mooclet is deleted (not yet implemented), or the experiment requires re-assignment at a certain time point.

    mooclets = list(MOOClet.find(
        {
            'studyId': study['_id'],
        }, {'_id': 1}
    ))

    # Find the latest interaction.
    the_interaction = Interaction.find_one({
        'user': user,
        'moocletId': {'$in': [mooclet['_id'] for mooclet in mooclets]}
    })

    if the_interaction is not None:
        the_mooclet = MOOClet.find_one({'_id': the_interaction['moocletId']})
        return (the_mooclet)
    else:
        root_mooclet = MOOClet.find_one({"_id": study['rootMOOClet']})
        return inductive_get_mooclet(root_mooclet, user)

def assign_treatment(deployment_name, study_name, user, where = None, other_information = None):
    try:
        start_time = time.time()
        the_mooclet = get_mooclet_for_user(deployment_name, study_name, user)
        mooclet = create_mooclet_instance(the_mooclet)
        version_to_show = mooclet.choose_arm(user, where, other_information)
        
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



def give_variable_value(variableName, user, value, where = None, other_information = None):
    current_time = datetime.datetime.now()
    the_variable = {
        "variableName": variableName,
        "user": user,
        "value": value,
        "where": where,
        "other_information": other_information,
        "timestamp": current_time
    }
    VariableValue.insert_one(the_variable)

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
            doc = Variable.find_one({"name": variableName})
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
    my_deployments = Deployment.find({"collaborators": {"$in": [user]}})
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
        the_Deployment = Deployment.find_one({"name": name})
        if the_Deployment is not None:
            return json_util.dumps({
                "status_code": 400,
                "message": "Deployment name is already used."
            }), 400
        else:
            Deployment.insert_one({
                "name": name,
                "description": description,
                "collaborators": collaborators,
            })
            return json_util.dumps({
                "status_code": 200,
                "message": "Deployment is created."
            }), 200
        


# {"studyName":"sim","description":"test2 description","mooclets":[{"id":1,"parent":0,"droppable":true,"isOpen":true,"text":"mooclet1","name":"mooclet1","policy":"ThompsonSamplingContextual","parameters":{"batch_size":1,"variance_a":1,"variance_b":5,"uniform_threshold":1,"precision_draw":1,"updatedPerMinute":0,"include_intercept":true,"coef_cov":[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],"coef_mean":[0,0,0,0],"regressionFormulaItems":[[{"name":"test","index":0}],[{"name":"version1","content":"v1"}],[{"name":"test","index":0},{"name":"version1","content":"v1"}]]},"weight":100}],"variables":[{"name":"test","index":0}],"versions":[{"name":"version1","content":"v1"},{"name":"version2","content":"v2"}]}

def convert_mooclet_tree_to_list(mooclet, myId, parentId, mooclet_list):
    mooclet_list.append({
        "id": myId,
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
    new_id = myId
    print(mooclet)
    for child in mooclet["children"]:
        new_id += 1
        child_mooclet = MOOClet.find_one({"_id": child}, {'createdAt': 0})
        convert_mooclet_tree_to_list(child_mooclet, new_id, myId, mooclet_list)


def build_json_for_study(studyId):
    the_study = Study.find_one({"_id": studyId})
    the_root_mooclet = MOOClet.find_one({"_id": the_study["rootMOOClet"]}, {'createdAt': 0})
    mooclet_list = []
    convert_mooclet_tree_to_list(the_root_mooclet, 1, 0, mooclet_list)
    print(mooclet_list)
    return

build_json_for_study(ObjectId("647a661c7c9b18cd1e4312d6"))