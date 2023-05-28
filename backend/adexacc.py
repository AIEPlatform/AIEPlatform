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


import random
def get_treatment(deployment, study, user):
    # TODO
    def inductive_get_treatment(mooclet, study):
        print(mooclet)
        if mooclet['policy'] == 'choose_mooclet':
            keys = list(mooclet['parameters'].keys())
            chances = list(mooclet['parameters'].values())
            random_key = random.choices(keys, chances)[0]
            next_mooclet = MOOClet.find_one({'name': random_key, 'study': study})
            inductive_get_treatment(next_mooclet, study)
        else:
            # this is a leaf node. we should get a version from it!
            print(mooclet['name'])
    study = Study.find_one({'deployment': deployment, 'name': study})
    rootMOOClet = study['rootMOOClet']
    the_root_mooclet = MOOClet.find_one({'name': rootMOOClet, 'study': study['name']})
    inductive_get_treatment(the_root_mooclet, study['name'])
    return 'version1'

get_treatment('test', 'test_study', 'student')