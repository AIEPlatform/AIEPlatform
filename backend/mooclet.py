from flask import Blueprint, session
from bson import json_util
from flask import request
from flask import send_file, make_response
import pandas as pd
import requests
import json
import numpy as np
from psycopg2.extensions import AsIs
from credentials import *
from AnalysisScript.default_table import default_table
import pickle

mooclet_apis = Blueprint('mooclet_apis', __name__)


# I will not ask for policy at this stage
def get_mooclet_id(mooclet_name):
    headers = {
        'Authorization': MOOCLET_TOKEN, 
        'Content-Type': 'application/json'
    }
    # TODO: how many mooclet it returns?
    response = requests.get(
        f'{MOOCLET_ENGINE_URL}/mooclet', headers=headers)

    everything = []
    page=1
    while 'results' in response.json():
        everything += response.json()['results']
        page+=1
        response = requests.get(
        f'{MOOCLET_ENGINE_URL}/mooclet?page={page}', headers=headers)
    mooclets = everything
    for mooclet in mooclets:
        if mooclet['name'] == mooclet_name:
            return mooclet['id']
    return None

def get_policy_id(policy_name):
    headers = {
        'Authorization': MOOCLET_TOKEN, 
        'Content-Type': 'application/json'
    }
    # TODO: how many mooclet it returns?
    response = requests.get(
        f'{MOOCLET_ENGINE_URL}/policy', headers=headers)
    everything = []
    page=1
    while 'results' in response.json():
        everything += response.json()['results']
        page+=1
        response = requests.get(
        f'{MOOCLET_ENGINE_URL}/policy?page={page}', headers=headers)
    policies = everything
    for policy in policies:
        if policy['name'] == policy_name:
            return policy['id']
    return None
        
def get_versions(mooclet_name): 
    mooclet_id = get_mooclet_id(mooclet_name)
    headers = {
        'Authorization': MOOCLET_TOKEN, 
        'Content-Type': 'application/json'
    }
    results = []
    response = requests.get(
        f'{MOOCLET_ENGINE_URL}/version', headers=headers)
    everything = []
    page=1
    while 'results' in response.json():
        everything += response.json()['results']
        page+=1
        response = requests.get(
        f'{MOOCLET_ENGINE_URL}/version?page={page}', headers=headers)
    versions = everything
    for version in versions:
        if version['mooclet'] == mooclet_id:
            results.append(version)
    return results

def get_policyparameters(mooclet_name): 
    mooclet_id = get_mooclet_id(mooclet_name)
    headers = {
        'Authorization': MOOCLET_TOKEN, 
        'Content-Type': 'application/json'
    }
    results = []
    response = requests.get(
        f'{MOOCLET_ENGINE_URL}/policyparameters', headers=headers)
    everything = []
    page=1
    while 'results' in response.json():
        everything += response.json()['results']
        page+=1
        response = requests.get(
        f'{MOOCLET_ENGINE_URL}/policyparameters?page={page}', headers=headers)
    policyparameters = everything
    for policyparameter in policyparameters:
        if policyparameter['mooclet'] == mooclet_id:
            results.append(policyparameter)
    return results


def get_variables(): 
    headers = {
        'Authorization': MOOCLET_TOKEN, 
        'Content-Type': 'application/json'
    }
    response = requests.get(
        f'{MOOCLET_ENGINE_URL}/variable', headers=headers)
    everything = []
    page=1
    while 'results' in response.json():
        everything += response.json()['results']
        page+=1
        response = requests.get(
        f'{MOOCLET_ENGINE_URL}/variable?page={page}', headers=headers)

    return everything

def create_mooclet(name):
    headers = {
        'Authorization': MOOCLET_TOKEN, 
        'Content-Type': 'application/json'
    }
    data = json.dumps({
        'name': name, 
        'policy': get_policy_id('choose_policy_group')
        })
    response = requests.post(
        f'{MOOCLET_ENGINE_URL}/mooclet', 
        data = data, 
        headers = headers)
    print('*** API to create MOOClet ***')
    print(f'{MOOCLET_ENGINE_URL}/mooclet')
    print(data)
    print(headers)
    print('***')
    print(response)
    if response.json()['name'] == name:
        print(f'MOOClet {name} is created.')
    else:
        print('MOOClet not created. Please try again or use a different mooclet name!')

def create_policy(mooclet_name, policy_name = 'choose_policy_group', parameters = None, contextual_variables = [], reward_variable = "", 
ts_configurable_parameters = None, ts_contextual_coef_cov_scale = 1, **other_parameters):
    mooclet_id = get_mooclet_id(mooclet_name)
    policy_id = get_policy_id(policy_name)
    if mooclet_id is None: return ('Please check your mooclet name.')
    if policy_id is None: return ('Please check your policy name.')

    versions = get_versions(mooclet_name)

    if len(versions) == 0: return ('Please create some versions first!')

    print(f'You have {len(versions)} versions.')
    policyparameters = get_policyparameters(mooclet_name)
    for policyparameter in policyparameters:
        if policyparameter['policy'] == policy_id:
            print(f'You have this policy already, due to the limitation of MOOClet, we need to delete this policyparameter first and then create this one for one.')
            headers = {
                'Authorization': MOOCLET_TOKEN, 
                'Content-Type': 'application/json'
            }
            response = requests.delete(
                f'{MOOCLET_ENGINE_URL}/policyparameters/{policyparameter["id"]}', 
                headers = headers)

    if policy_name == 'choose_policy_group':
        try:
            if sum(parameters.values()) != 1:
                print("Please make sure the values sum to 1.")
            else:
                headers = {
                    'Authorization': MOOCLET_TOKEN, 
                    'Content-Type': 'application/json'
                }
                data = json.dumps({
                        "mooclet": mooclet_id,
                        "policy": policy_id,
                        "parameters": {"policy_options": parameters}
                    })
                response = requests.post(
                    f'{MOOCLET_ENGINE_URL}/policyparameters', 
                    data = data, 
                    headers = headers)
                
                print('*** API to create choose policy group paratemers ***')
                print(f'{MOOCLET_ENGINE_URL}/policyparameters')
                print(data)
                print(headers)
                print('***')
        except:
            print("Please make sure the parameters is in good format.")

    elif policy_name == 'weighted_random': 
        try:
            
            all_valid_version_name = True
            for version in versions:
                if version['name'] not in parameters.keys():
                    all_valid_version_name = False
                    break
            if not all_valid_version_name: 
                print("Please make sure that the version name is tied to the mooclet.")
            print(parameters)
            if sum(parameters.values()) != 1:
                print("Please make sure the values sum to 1.")
            else:
                headers = {
                    'Authorization': MOOCLET_TOKEN, 
                    'Content-Type': 'application/json'
                }
                data = json.dumps({
                        "mooclet": mooclet_id,
                        "policy": policy_id,
                        "parameters": {"probability_distribution": parameters}
                    })
                print(data)

                response = requests.post(
                    f'{MOOCLET_ENGINE_URL}/policyparameters', 
                    data = data, 
                    headers = headers)

                print('*** API to create choose weighted random paratemers ***')
                print(f'{MOOCLET_ENGINE_URL}/policyparameters')
                print(data)
                print(headers)
                print('***')
        except Exception as e:
            print(e)
            print("Please make sure the parameters is in good format.")

    elif policy_name == 'thompson_sampling_contextual':
        version_control_flags = list(versions[0]["version_json"].keys())
        if True: 
            # intercept
            coef_cov = np.zeros((len(version_control_flags) + len(version_control_flags) * (len(contextual_variables)) + 1 + 1, len(version_control_flags) + len(version_control_flags) * (len(contextual_variables)) + 1 + 1), int)
            np.fill_diagonal(coef_cov, ts_contextual_coef_cov_scale)
            coef_cov = coef_cov.tolist()
            coef_mean = [0] * (len(version_control_flags) + len(version_control_flags) * (len(contextual_variables)) + 1 + 1)
        else:
            coef_cov = np.identify(len(version_control_flags) + len(version_control_flags) * (len(contextual_variables)) + 1).tolist()
            coef_mean = [0] * (len(version_control_flags) + len(version_control_flags) * (len(contextual_variables)) + 1)

        regression_formula = ""
        regression_formula += reward_variable
        regression_formula += " ~ "
        action_space = {}
        for i in range(0, len(version_control_flags)):
            regression_formula += f'{version_control_flags[i]} + {version_control_flags[i]} * {contextual_variables[0]} + '
            action_space[version_control_flags[i]] = [0, 1]
            # TODO: Currently only support ONE contextual variable
        regression_formula += contextual_variables[0]
        contextual_variables = ["version"] + contextual_variables

        parameters = {"coef_cov": coef_cov, "coef_mean": coef_mean, "batch_size": 20, "variance_a": 2, "variance_b": 1, "action_space": action_space, "precesion_draw": 1, "outcome_variable": reward_variable, "include_intercept": 1, "uniform_threshold": 0, "regression_formula": regression_formula, "contextual_variables": contextual_variables}
        for key in other_parameters:
          parameters[key] = other_parameters[key]


        headers = {
            'Authorization': MOOCLET_TOKEN, 
            'Content-Type': 'application/json'
        }
        data = json.dumps({
                "mooclet": mooclet_id,
                "policy": policy_id,
                "parameters": parameters
            })

        response = requests.post(
            f'{MOOCLET_ENGINE_URL}/policyparameters', 
            data = data, 
            headers = headers)
        
        print('*** API to create TS Contextual paratemers ***')
        print(f'{MOOCLET_ENGINE_URL}/policyparameters')
        print(data)
        print(headers)
        print('***')

        # check if contextual variable and reward exist.
        variables = get_variables()
        variable_names = [variable['name'] for variable in variables]

        for contextual_variable in contextual_variables:
            if contextual_variable not in variable_names:
                print(f'You don\'t have {contextual_variable}, I automatically created one for you!')
                headers = {
                    'Authorization': MOOCLET_TOKEN, 
                    'Content-Type': 'application/json'
                }
                data = json.dumps({
                    'name': contextual_variable
                    })
                response = requests.post(
                    f'{MOOCLET_ENGINE_URL}/variable', 
                    data = data, 
                    headers = headers)
                
                print('*** API to create variable ***')
                print(f'{MOOCLET_ENGINE_URL}/variable')
                print(data)
                print(headers)
                print('***')
        if reward_variable not in variable_names:
            print(f'You don\'t have {reward_variable}, I automatically created one for you!')
            headers = {
                'Authorization': MOOCLET_TOKEN, 
                'Content-Type': 'application/json'
            }
            data = json.dumps({
                'name': reward_variable
                })
            response = requests.post(
                f'{MOOCLET_ENGINE_URL}/variable', 
                data = data, 
                headers = headers)
            print('*** API to create variable ***')
            print(f'{MOOCLET_ENGINE_URL}/variable')
            print(data)
            print(headers)
            print('***')


    elif policy_name == 'ts_configurable':

        parameters = {"prior": {"failure": 1, "success": 1}, "batch_size": 4, "max_rating": 1, "min_rating": 0, "uniform_threshold": 8, "outcome_variable_name": reward_variable} if ts_configurable_parameters is None else ts_configurable_parameters

        for key in other_parameters:
          parameters[key] = other_parameters[key]
        headers = {
            'Authorization': MOOCLET_TOKEN, 
            'Content-Type': 'application/json'
        }
        data = json.dumps({
                "mooclet": mooclet_id,
                "policy": policy_id,
                "parameters": parameters
            })

        response = requests.post(
            f'{MOOCLET_ENGINE_URL}/policyparameters', 
            data = data, 
            headers = headers)

        print('*** API to create ts configurable parameters ***')
        print(f'{MOOCLET_ENGINE_URL}/policyparameters')
        print(data)
        print(headers)
        print('***')


        # check if contextual variable and reward exist.
        variables = get_variables()
        variable_names = [variable['name'] for variable in variables]
        if reward_variable not in variable_names:
            print(f'You don\'t have {reward_variable}, I automatically created one for you!')
            headers = {
                'Authorization': MOOCLET_TOKEN, 
                'Content-Type': 'application/json'
            }
            data = json.dumps({
                'name': reward_variable
                })
            response = requests.post(
                f'{MOOCLET_ENGINE_URL}/variable', 
                data = data, 
                headers = headers)
            
            print('*** API to create variable ***')
            print(f'{MOOCLET_ENGINE_URL}/variable')
            print(data)
            print(headers)
            print('***')
    elif policy_name == "uniform_random": 
        try:
            headers = {
                'Authorization': MOOCLET_TOKEN, 
                'Content-Type': 'application/json'
            }
            data = json.dumps({
                "mooclet": mooclet_id,
                "policy": policy_id
            })
            response = requests.post(
                f'{MOOCLET_ENGINE_URL}/policyparameters', 
                data = data, 
                headers = headers)

            print('*** API to create uniform random parameters ***')
            print(f'{MOOCLET_ENGINE_URL}/policyparameters')
            print(data)
            print(headers)
            print('***')

            variables = get_variables()
            variable_names = [variable['name'] for variable in variables]
            if reward_variable not in variable_names:
                print(f'You don\'t have {reward_variable}, I automatically created one for you!')
                headers = {
                    'Authorization': MOOCLET_TOKEN, 
                    'Content-Type': 'application/json'
                }
                data = json.dumps({
                    'name': reward_variable
                    })
                response = requests.post(
                    f'{MOOCLET_ENGINE_URL}/variable', 
                    data = data, 
                    headers = headers)
                print('*** API to create variable ***')
                print(f'{MOOCLET_ENGINE_URL}/variable')
                print(data)
                print(headers)
                print('***')
        except:
            print("Please make sure the parameters is in good format.")
def create_version(mooclet_name, version_name, text):
    mooclet_id = get_mooclet_id(mooclet_name)
    if mooclet_id is None: return ('Please check your mooclet name.')

    current_versions = get_versions(mooclet_name)
    key_values = str(bin(len(current_versions) + 1 - 1))[2:][::-1]
    num_keys = len(key_values)
    version_json = {}
    for num_key in range(1, num_keys + 1):
        version_json[f'{mooclet_name}_VERSIONS_CONTROL_FLAG{num_key}'] = int(key_values[num_key-1])

    for current_version in current_versions:
        if current_version['name'] == version_name:
            print("The version already exists.")
            return
    # Reset for the other versions.
    headers = {
        'Authorization': MOOCLET_TOKEN, 
        'Content-Type': 'application/json'
    }
    data = json.dumps({
        'mooclet': mooclet_id, 
        'name': version_name, 
        'text': text, 
        'version_json': version_json
        })
    response = requests.post(
        f'{MOOCLET_ENGINE_URL}/version', 
        data = data, 
        headers = headers)
    print('*** API to create version ***')
    print(f'{MOOCLET_ENGINE_URL}/version')
    print(data)
    print(headers)
    print('***')

    # TODO: will it always be sorted by the version id???
    new_num_keys = num_keys
    for i in range(0, len(current_versions)):
        version = current_versions[i]
        version_json = version['version_json']
        version_json[f'{mooclet_name}_VERSIONS_CONTROL_FLAG{new_num_keys}'] = 0

        # Reset for the other versions.
        headers = {
            'Authorization': MOOCLET_TOKEN, 
            'Content-Type': 'application/json'
        }
        data = json.dumps({
            'mooclet': mooclet_id, 
            'version_json': version_json, 
            'name': version['name'], 
            'text': version['text']
            })
        response = requests.put(
            f'{MOOCLET_ENGINE_URL}/version/{version["id"]}', 
            data = data, 
            headers = headers)
        print('*** API to change a version (PUT) ***')
        print(f'{MOOCLET_ENGINE_URL}/version')
        print(data)
        print(headers)
        print('***')
        print(response)

def delete_mooclet(mooclet_name):
    mooclet_id = get_mooclet_id(mooclet_name)
    policies = get_policyparameters(mooclet_name)
    versions = get_versions(mooclet_name)
    for policy in policies:
        headers = {
            'Authorization': MOOCLET_TOKEN, 
            'Content-Type': 'application/json'
        }
        response = requests.delete(
            f'{MOOCLET_ENGINE_URL}/policyparameters/{policy["id"]}', 
            headers = headers)
    for version in versions:
        headers = {
            'Authorization': MOOCLET_TOKEN, 
            'Content-Type': 'application/json'
        }
        response = requests.delete(
            f'{MOOCLET_ENGINE_URL}/version/{version["id"]}', 
            headers = headers)
    headers = {
        'Authorization': MOOCLET_TOKEN, 
        'Content-Type': 'application/json'
    }
    response = requests.delete(
        f'{MOOCLET_ENGINE_URL}/mooclet/{mooclet_id}', 
        headers = headers)
    

def create_variable(variable_name):
    variables = get_variables()
    variable_names = [variable['name'] for variable in variables]
    if variable_name not in variable_names:
        print(f'You don\'t have {variable_name}, I automatically created one for you!')
        headers = {
            'Authorization': MOOCLET_TOKEN, 
            'Content-Type': 'application/json'
        }
        data = json.dumps({
            'name': variable_name
            })
        response = requests.post(
            f'{MOOCLET_ENGINE_URL}/variable', 
            data = data, 
            headers = headers)
        print('*** API to create variable ***')
        print(f'{MOOCLET_ENGINE_URL}/variable')
        print(data)
        print(headers)
        print('***')
 
        return response

def update_policy_parameter(mooclet_id, policy_parameter_id, parameters):
        headers = {
            'Authorization': MOOCLET_TOKEN, 
            'Content-Type': 'application/json'
        }
        data = json.dumps({
                "parameters": parameters
            })

        response = requests.put(
            f'{MOOCLET_ENGINE_URL}/policyparameters/{policy_parameter_id}', 
            data = data, 
            headers = headers)



@mooclet_apis.route("/apis/create_and_init_mooclet", methods=["POST"])
def create_and_init_mooclet():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    data = request.get_json()
    mooclet_name = data['moocletName']
    create_mooclet(mooclet_name)
    arms = data['versions']
    for i in range(1, len(arms) + 1):
        create_version(data['moocletName'], f'{mooclet_name}_arm{str(i)}', arms[i-1]['content'])

    existing_policy_parameters = get_policyparameters(mooclet_name)
    variables = data['variables']
    for variable in variables:
        create_variable(variable['name'])
    
    # Policies!!!
    policies = data['policies']
    choose_policy_group_parameter = None
    if len(policies) == 1:
        choose_policy_group_parameter = {policies[0]['type']: 1.0}

    print(choose_policy_group_parameter)
    create_policy(mooclet_name, 'choose_policy_group', parameters = choose_policy_group_parameter)


    for policy in policies:
        parameter_raw = policy['parameter']
        parameter_policy = {}
        if policy['type'] == "weighted_random":
            for index, key in enumerate(parameter_raw):
                parameter_policy[f'{mooclet_name}_arm{str(index + 1)}'] = parameter_raw[key]
            create_policy(mooclet_name, policy['type'], parameters = parameter_policy)
            


    return json_util.dumps({
        "status_code": 200, 
        "message": "Create a MOOClet!"
    }), 200


@mooclet_apis.route("/apis/get_mooclets", methods=["GET"])
def get_mooclets():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    headers = {
        'Authorization': MOOCLET_TOKEN, 
        'Content-Type': 'application/json'
    }
    # TODO: how many mooclet it returns?
    print("hello world")
    response = requests.get(
        f'{MOOCLET_ENGINE_URL}/mooclet', headers=headers)

    everything = []
    page=1
    while 'results' in response.json():
        everything += response.json()['results']
        page+=1
        response = requests.get(
        f'{MOOCLET_ENGINE_URL}/mooclet?page={page}', headers=headers)
    mooclets = everything


    return json_util.dumps({
        "status_code": 200, 
        "message": "Get a list of MOOClets!", 
        "data": mooclets
    }), 200



@mooclet_apis.route("/apis/get_mooclet_information/<mooclet_id>", methods=["GET"])
def get_mooclet_information(mooclet_id):
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    cursor = conn.cursor()
    cursor.execute("select distinct(name) from (select * from engine_value where mooclet_id = %s) t1 JOIN engine_variable on (t1.variable_id = engine_variable.id);", [mooclet_id])
    variables = cursor.fetchall()

    cursor.execute("select distinct(name) from engine_version where mooclet_id = %s", [mooclet_id])
    versions = cursor.fetchall()

    cursor.close()
    # TODO: get other information, such as policy.
    return json_util.dumps({
        "status_code": 200, 
        "message": "Get mooclet information!", 
        "data": {
            "variables": variables,
            "versions": versions
        }
    }), 200

@mooclet_apis.route("/apis/analysis/simple_summary_versions", methods=["POST"])
def simple_summary_versions():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    data = request.get_json()
    mooclet_name = data['moocletName']
    variable_name = data['variableName'][0]
    contextual_name = data['contextName'][0] # Now we only support one contextual variable for this simple analysis.
    cursor = conn.cursor()
    # GET DATA
    cursor.execute("select id from engine_mooclet where name = %s;", [mooclet_name]);
    mooclet_id = cursor.fetchone()[0]

    cursor.execute("select id from engine_variable where name = %s;", [variable_name]);
    variable_id = cursor.fetchone()[0]
    print(mooclet_id)
    print(variable_name)


    cursor.execute("CREATE TEMPORARY VIEW rewards AS SELECT t1.id AS reward_id, value AS reward, engine_version.name, t1.timestamp, t1.learner_id, t1.policy_id, t1.version_id from (select * from engine_value where variable_id = %s AND mooclet_id = %s) t1 JOIN engine_version on t1.version_id = engine_version.id;", [variable_id, mooclet_id])

    cursor.execute("select id from engine_variable where name = %s;", [contextual_name]);
    contextual_id = cursor.fetchone()[0]

    cursor.execute("CREATE TEMPORARY VIEW wanted_contextual AS SELECT value, learner_id as contextual_learner_id, timestamp as contextual_timestamp FROM engine_value where variable_id = %s", [contextual_id])

    cursor.execute("CREATE TEMPORARY VIEW reward_contextual_joined AS SELECT * FROM rewards LEFT JOIN wanted_contextual ON learner_id = wanted_contextual.contextual_learner_id WHERE contextual_timestamp < timestamp;")

    cursor.execute("CREATE TEMPORARY VIEW reward_with_latest_contextual_timestamp AS (SELECT reward_id, learner_id, reward, MAX(contextual_timestamp) AS contextual_timestamp, policy_id FROM reward_contextual_joined GROUP BY (reward_id, learner_id, reward, policy_id)) UNION (SELECT reward_id, learner_id, reward, contextual_timestamp, policy_id FROM reward_contextual_joined where contextual_timestamp is NULL);")

    cursor.execute("CREATE TEMPORARY VIEW reward_with_latest_contextual AS SELECT reward_with_latest_contextual_timestamp.reward_id, reward_with_latest_contextual_timestamp.learner_id, reward_with_latest_contextual_timestamp.reward, reward_contextual_joined.timestamp, reward_with_latest_contextual_timestamp.contextual_timestamp, value AS %s, reward_contextual_joined.policy_id, version_id FROM reward_with_latest_contextual_timestamp JOIN reward_contextual_joined ON reward_with_latest_contextual_timestamp.reward_id = reward_contextual_joined.reward_id AND reward_with_latest_contextual_timestamp.contextual_timestamp = reward_contextual_joined.contextual_timestamp;", [AsIs(contextual_name)])



    cursor.execute("CREATE TEMPORARY VIEW result AS SELECT reward_id, learner_id, reward, timestamp, contextual_timestamp, %s, policy_id, engine_version.name as version FROM reward_with_latest_contextual JOIN engine_version ON reward_with_latest_contextual.version_id = engine_version.id;", [AsIs(contextual_name)])


    cursor.execute("select * from result;")
    values = cursor.fetchall()
    df = pd.DataFrame(data = values, columns= ['reward_id', 'learner_id', 'reward', 'timestamp', 'contextual_timestamp', contextual_name, 'policy_id', 'version'])
    df.to_csv("test.csv", index = False)

    df1 = pd.read_csv('test.csv')

    # assume policy_id is different arms
    cont_name=contextual_name
    arm_col_name='version'
    df0=df1[['reward',cont_name,arm_col_name]]
    # df0=df0.astype('float')
    df0.dtypes
    df_mean=df0.groupby([cont_name,arm_col_name]).mean()

    df_count=df0.groupby([cont_name,arm_col_name]).count()

    df_sd=df0.groupby([cont_name,arm_col_name]).std()
    df_output=pd.concat([df_mean,df_count,df_sd],axis=1)
    df_output.columns=['mean','count','std']


    df_output=df_output.reindex(pd.MultiIndex.from_product([sorted(df0[cont_name].unique()),sorted( df0[arm_col_name].unique())],names=[cont_name, arm_col_name]))
    df_output.to_csv("temp.csv")
    df = pd.read_csv("temp.csv")
    df['mean'] = df['mean'].round(2)
    df['std'] = df['std'].round(2)
    df = df.fillna('')
    tuples = [tuple(x) for x in df.values]
    tuples


    # cursor.execute("select * from reward_with_latest_contextual;")
    # values = cursor.fetchall()
    # df = pd.DataFrame(data = values, columns = ['reward_id', 'learner_id', 'reward', 'timestamp', 'contextual_timestamp', contextual_name])
    # print(df)
    # print(mooclet_id)
    # df = pd.DataFrame(data = values, columns = ['reward', 'version', 'timestamp', 'leaner_id'])
    # print(df)
    # result = df.groupby('version').agg(['count','mean'])

    # TODO: get other information, such as policy.
    cursor.close()
    return json_util.dumps({
        "status_code": 200, 
        "message": "Get mooclet information!",
        "data": tuples
    }), 200

@mooclet_apis.route("/apis/get_datasets", methods=["GET"])
def get_datasets():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    datasets = Dataset.find({},{"dataset":0})
    return json_util.dumps({
        "status_code": 200, 
        "message": "Get datasets!",
        "data": datasets
    }), 200


@mooclet_apis.route("/apis/data_downloader/<datasetDescription>", methods=["GET"])
def data_downloader(datasetDescription):
    # GET DATA
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    try:
        print(datasetDescription)
        dataset = Dataset.find_one({"datasetDescription": datasetDescription})
        df = pickle.loads(dataset['dataset'])
        csv_string = df.to_csv(index=False)

        # Create a Flask response object with the CSV data
        response = make_response(csv_string)

        # Set the headers to tell the browser to download the file as a CSV
        response.headers['Content-Disposition'] = 'attachment; filename=data.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 400, 
            "message": e
        }), 500
    

@mooclet_apis.route("/apis/upload_local_dataset", methods=["POST"])
def upload_local_dataset():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    # GET DATA
    csv_file = request.files['csvFile']
    df = pd.read_csv(csv_file)
    dataset_description = request.form['datasetDescription']
    # Do something with the DataFrame, e.g. print its contents
    data_dict = df.to_dict('records')

    # Create document dictionary
    myquery = { "datasetDescription": dataset_description }
    newvalues = { "$set": { "dataset": data_dict } }

    Dataset.update_one(myquery, newvalues)
    try:
        return json_util.dumps({
            "status_code": 200, 
            "message": "Done"
        }), 200
    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500
    

@mooclet_apis.route("/apis/data_deletor/<datasetDescription>", methods=["DELETE"])
def data_deletor(datasetDescription):
    # GET DATA
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    try:
        Dataset.delete_one({"datasetDescription": datasetDescription})
        datasets = Dataset.find({},{"dataset":0})
        return json_util.dumps({
            "status_code": 200, 
            "message": "Deleted", 
            "data": datasets
        }), 200
    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500
    

@mooclet_apis.route("/apis/availableVariables", methods=["GET"])
def availableVariables():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    # GET DATA
    cursor = conn.cursor()
    try:
        results = []
        
        cursor.execute("select name from engine_variable;")
        for row in cursor:
            results.append({"name": row[0]})

        cursor.close()
        return json_util.dumps({
            "status_code": 200, 
            "data": results
        }), 200        
    except Exception as e:
        print(e)
        cursor.close()
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500


# FOR OLD MOOCLET
@mooclet_apis.route("/apis/createNewVariable", methods=["POST"])
def createNewVariable():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    try:
        data = request.get_json()
        new_variable_name = data['newVariableName']
        response = create_variable(new_variable_name)
        if response is None:
            return json_util.dumps({
                "status_code": 400, 
                "message": "The variable name exists or the variable name is not valid."
            }), 400
        else:
            return json_util.dumps({
                "status_code": 200, 
                "message": "The variable name is created sucessfully and linked to the mooclet-to-be-create."
            }), 200

    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500
    

@mooclet_apis.route("/apis/getMOOCletVersionsPolicies/<MOOCletName>", methods=["GET"])
def getMOOCletVersionsPolicies(MOOCletName):
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    try:
        versions = get_versions(MOOCletName)
        policyparameters = get_policyparameters(MOOCletName)
        return json_util.dumps({
            "status_code": 200, 
            "versions": versions, 
            "policyparameters": policyparameters
        }), 200
    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 500, 
            "message": e
        }), 500
    


@mooclet_apis.route("/apis/analysis_default_table/get_contextual_variables", methods=["GET"])
def get_contextual_variables():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    datasetDescription = request.args.get('datasetDescription')
    if datasetDescription is None:
        #TODO
        pass

    dataset = Dataset.find_one({"datasetDescription": datasetDescription})
    df = pickle.loads(dataset['dataset'])

    context_columns = [c for c in list(df.columns) if c.startswith("context_value_") and c.startswith("context_value_id_") is False]

    return json_util.dumps({
        "status_code": 200,
        "data": context_columns
    })


@mooclet_apis.route("/apis/analysis_default_table", methods=["GET"])
def analysis_default_table():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    datasetDescription = request.args.get('datasetDescription')
    contextualVariable = request.args.get('contextualVariable')
    if datasetDescription is None or contextualVariable is None:
        #TODO
        pass

    dataset = Dataset.find_one({"datasetDescription": datasetDescription})
    df = pickle.loads(dataset['dataset'])
    result_table = default_table(df, contextualVariable)
    return json_util.dumps({
        "status_code": 200,
        "columns": list(result_table.columns), 
        "rows": [tuple(r) for r in result_table.to_numpy()]
    })

@mooclet_apis.route("/apis/hello_world", methods=["GET"])
def hello_world():
    return json_util.dumps({
        "status_code": 200, 
        "message": "Hello World."
    }), 200






# BELOW IS FOR THE NEW dataarrow
import datetime

def get_username():
    return "chenpan"

@mooclet_apis.route("/apis/variables", methods=["GET"])
def get_variables():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    try:
        username = get_username()
        variables = Variable.find({"owner": username})
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

@mooclet_apis.route("/apis/variable", methods=["POST"])
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
        doc = Variable.find_one({"name": new_variable_name})
        if doc is not None:
            return json_util.dumps({
                "status_code": 400, 
                "message": "The variable name exists."
            }), 400
        Variable.insert_one({
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
    