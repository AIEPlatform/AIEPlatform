from credentials import *

def check_duplicated(collection, field, value):
    # TODO
    doc = list(collection.find({field: value}))
    if len(doc) > 0: return True
    return False

def is_collaborator(deployment_id, user_id):
    # TODO
    return True

def is_auth():
    # TODO
    return True

# Create a deployment with no study
def create_deployment(name, description, collaborators):
    if not is_auth(): return False
    if len(collaborators) == 0: return False
    if check_duplicated(Deployment, 'name', name): return False
    new_deployment = {
        'name': name,
        'description': description,
        'collaborators': collaborators
    }
    Deployment.insert_one(new_deployment)

# Add study to a deployment
def add_study(name, versions, variables, mooclets, deployment, user):
    # TODO: check if study exists
    if not is_auth(): return False
    if not is_collaborator(deployment, user): return False
    doc = Study.find_one({'deployment': deployment, 'name': name})
    if doc is not None: return False

    # TODO: USE TRANSACTION TO MAKE SURE WE CAN UNDO IF ANYTHING GOES WRONG!!!!!
    def create_mooclet(mooclet):
        for child in mooclet['children']:
            create_mooclet(child)

        doc = MOOClet.find_one({'name': mooclet['name'], 'study': name})
        if doc is not None: return doc['name']

        new_mooclet = {
            "name": mooclet['name'],
            "policy": mooclet['policy'],
            "parameters": mooclet['parameters'],
            "study": name,
            "isConsistent": False, 
            "updatedPerMinute": False, 
            "autoZeroPerMinute": False
        }

        MOOClet.insert_one(new_mooclet)
        return mooclet['name']
    
    root_mooclet = create_mooclet(mooclets)
    the_study = {
        'name': name,
        'deployment': deployment,
        'versions': versions,
        'variables': variables,
        'rootMOOClet': root_mooclet
    }
    # Induction to create mooclet
    Study.insert_one(the_study)


    # versions: {
    # 'version1': text, 
    # 'version2': text
    # }

    # variables: [
    # {name, type, minValue, maxValue}, ...
    # ]

    # mooclets: 
    # {name, parameters, children = []}
    # 

mooclets = {
    'name': 'top_level_choose_mooclet', 
    'policy': 'choose_mooclet',
    'parameters': {
        'uniform_random1': 0.4,
        'ts_contextual1': 0.6
    },
    'children': [
        {
            'name': 'uniform_random1', 
            'policy': 'uniform_random',
            'parameters': {
            }, 
            'children': []
        },
        {
            'name': 'ts_contextual1', 
            'policy': 'ts_contextual',
            'parameters': {
                'contextual_variables': ['contextual1', 'contextual2'], 
                'regression_formula': 'reward ~ contextual1 * version1 + contextual2 * version1 + version1 + contextual1 + contextual2', 
                'include_intercept': 1,
                'uniform_threshold': 0, 
                'precesion_draw': 1, 
                'coef_cov': [[10, 0, 0, 0], [0, 10, 0, 0], [0, 0, 10, 0], [0, 0, 0, 10]], 
                'coef_mean': [0, 0, 0, 0],
                "batch_size": 2, 
                "variance_a": 2, 
                "variance_b": 1
            }, 
            'children': []
        }
    ]
}

versions = {
    'version1': 'this is version 1',
    'version2': 'this is version 2'
}

variables = [
    {
        'name': 'contextual1', 'type': 'integer', 'minValue': 0, 'maxValue': 1
    }, 
    {
        'name': 'contextual2', 'type': 'integer', 'minValue': 0, 'maxValue': 1
    }
]

create_deployment('test', 'this is a test', ['chenpan'])
add_study('test_study', versions, variables, mooclets, 'test', 'chenpan')

from flask import Blueprint, session
from flask import request
from bson import json_util
from bson.objectid import ObjectId
adexacc_apis = Blueprint('adexacc_apis', __name__)

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
        "updatedPerMinute": False, 
        "autoZeroPerMinute": False, 
        "children": my_children, 
        "weight": mooclet['weight']
    }

    response = MOOClet.insert_one(new_mooclet, session=session)
    return response.inserted_id

@adexacc_apis.route("/apis/study", methods=["POST"])
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

    doc = Study.find_one({'deploymentId': deploymentId, 'name': study_name})
    if doc is not None: 
        return json_util.dumps({
            "status_code": 404, 
            "message": "Study name already exists."
        }), 404

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




import random
from helpers import *
from policy import *
def assign_treatment(deployment_name, study_name, user):
    # TODO
    def inductive_get_treatment(mooclet, versions, variables, user):
        if len(mooclet['children']) > 0:
            children = MOOClet.find({"_id": {"$in": mooclet['children']}}, {"_id": 1, "weight": 1})

            # TODO: Check previous assignment. Choose MOOClet should be consistent with previous assignment.
            next_mooclet_id = random_by_weight(list(children))['_id']
            next_mooclet = MOOClet.find_one({'_id': next_mooclet_id})
            print(next_mooclet)
            inductive_get_treatment(next_mooclet, versions, variables, study)
        else:
            # this is a leaf node. we should get a version from it!
            # print(mooclet['name'])
            
            #TODO: Write into modular.
            if mooclet['policy'] == "uniform_random":
                version_to_show = uniform_random_assign_treatment(mooclet, versions, variables, user)
                return version_to_show
            pass

    deployment = Deployment.find_one({'name': deployment_name})
    study = Study.find_one({'deploymentId': ObjectId(deployment['_id']), 'name': study_name})
    versions = study['versions']
    variables = study['variables']
    root_mooclet = MOOClet.find_one({"_id": study['rootMOOClet']})
    return inductive_get_treatment(root_mooclet, versions, variables, user)


def get_reward(deployment_name, study_name, user, value):
    # Get MOOClet!
    study = Study.find_one({'deploymentId': ObjectId(deployment['_id']), 'name': study_name})
    mooclets_of_this_study = MOOClet.find({'studyId': study['_id']})

assign_treatment(deployment_name = 'test', study_name = 'test2 study', user = 'student')