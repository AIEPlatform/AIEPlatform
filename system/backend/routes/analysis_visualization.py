from credentials import *
from flask import Blueprint, session
from flask import request
from bson import json_util
from bson.objectid import ObjectId
from helpers import *
from Models.DeploymentModel import DeploymentModel
from Models.DatasetModel import DatasetModel
from Models.StudyModel import StudyModel
from Models.InteractionModel import InteractionModel
from flatten_json import flatten
import pickle
import smtplib
from email.mime.text import MIMEText
import re
import datetime
from errors import *
import pandas as pd
import pickle
from bson.objectid import ObjectId
from flask import send_file, make_response
from collections import Counter

import os
import importlib.util
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Create a function to load a policy module
def load_policy_module(policy_name):
    policy_path = os.path.join("../plugins/analysis", policy_name)
    algorithm_module_path = os.path.join(policy_path, "backend", "analysis.py")
    
    if os.path.isfile(algorithm_module_path):
        module_name = f"{policy_name}"
        spec = importlib.util.spec_from_file_location(module_name, algorithm_module_path)
        algorithm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(algorithm_module)
        policy_class = getattr(algorithm_module, policy_name, None)
        return policy_class
    else:
        return None

# Create a function to reload the analysis classes
def reload_analysis_classes():
    global analysis_classes
    analysis_classes = {policy_name: load_policy_module(policy_name) for policy_name in os.listdir("../plugins/analysis") if os.path.isdir(os.path.join("../plugins/analysis", policy_name))}

# Create a watchdog event handler to watch for file changes
class PluginChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            # Reload the analysis classes when a directory is modified
            reload_analysis_classes()

# Create an observer to watch the plugin directory
observer = Observer()
observer.schedule(PluginChangeHandler(), path="../plugins/analysis", recursive=True)
observer.start()

# Initial loading of analysis classes
reload_analysis_classes()

analysis_visualization_apis = Blueprint('analysis_visualization_apis', __name__)

@analysis_visualization_apis.route("/apis/upload_local_modification", methods = ["PUT"])
def upload_local_modification():

    csv_file = request.files['csvFile']
    df = pd.read_csv(csv_file)

    print(df['outcome.timestamp'])

    datasetId = request.form['datasetId'] if 'datasetId' in request.form else None

    response = DatasetModel.update_one(datasetId, df)

    if response == 200:
        return status_code("UPLOAD_LOCAL_MODIFICATION_SUCCESSFUL")
    else:
        # TODO
        return status_code("DEFAULT_SERVER_ERROR")





@analysis_visualization_apis.route("/apis/analysis/downloadArrowDataset/<id>", methods=["GET"])
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






@analysis_visualization_apis.route("/apis/analysis/deleteArrowDataset/<id>", methods=["DELETE"])
def delete_arrow_dataset(id):
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status": 403,
        }), 403 
    
    try:
        dataset = DatasetModel.delete(ObjectId(id))
        return json_util.dumps({
            "status": 200,
            "message": "Dataset is deleted."
        }), 200
    except:
        return json_util.dumps({
            "status": 500, 
            "message": "deleting error"
        }), 500
    

@analysis_visualization_apis.route("/apis/analysis/updateArrowDataset/<id>", methods=["PUT"])
def update_arrow_dataset(id):
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status": 403,
        }), 403 
    
    try:
        dataset = DatasetModel.get_one({"_id": 
                                        ObjectId(id)})
        deploymentId = dataset['deploymentId']
        study = dataset['study']
        theDeployment = DeploymentModel.get_one({"_id": ObjectId(deploymentId)})
        deployment = theDeployment['name']
        theStudy = StudyModel.get_one({"name": study, "deploymentId": deploymentId})

        if Counter(dataset['variables']) == Counter(theStudy['variables']):
            df = create_df_from_mongo(study, deployment)
            if len(df) == 0:
                return json_util.dumps({
                    "status": 400,
                    "message": "Dataset is empty, can't update."
                }), 400      
            _ = DatasetModel.update_one(ObjectId(id), df)
            the_deployment = DeploymentModel.get_one({"name": deployment})
            the_datasets = DatasetModel.get_many({"deploymentId": the_deployment['_id']}, {'dataset': 0})
            updatedDataset = DatasetModel.get_one({"_id": ObjectId(id)})

            return json_util.dumps(
                {
                "status": 200,
                "datasets": the_datasets, 
                "dataset": updatedDataset
                }
            ), 200
        else:
            return json_util.dumps({
                "status": 400,
                "message": "We can't update a dataset that has different variables. Please create a new one instead."
            }), 400     
    except Exception as e:
        print(e)
        return json_util.dumps({
            "status": 500, 
            "message": "update error"
        }), 500
    





@analysis_visualization_apis.route("/apis/analysis/get_deployment_datasets", methods=["GET"])
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


@analysis_visualization_apis.route("/apis/analysis/analysis", methods = ["POST"])
def analysis():
    theDatasetId = request.json['theDatasetId'] if 'theDatasetId' in request.json else None # This is the id.
    
    info = request.json['info'] if 'info' in request.json else {}

    analytics_name = request.json['analysisType'] if 'analysisType' in request.json else None
    if analytics_name is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure analyticsName is provided."
        }), 400
    
    if analytics_name not in analysis_classes:
        return json_util.dumps({
            "status_code": 400,
            "message": "The analysis is not supported yet. Make sure that you have loaded the plugin."
        }), 400
    AnalysisClass = analysis_classes[analytics_name]
 
    if theDatasetId is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure the_study_basic_info, selected_variables are provided."
        }), 400
    else:
        df = getDataset(theDatasetId)
        info['df'] = df
        analysis_instance = AnalysisClass(info)
        the_result = analysis_instance.analysis()
        return json_util.dumps({
            "status_code": 200,
            "message": "Table returned.",
            "result": the_result
        }), 200

def create_df_from_mongo(study_name, deployment_name):
    the_deployment = DeploymentModel.get_one({"name": deployment_name})
    the_study = StudyModel.get_one({"name": study_name, "deploymentId": the_deployment['_id']})

    result = InteractionModel.get_interactions_all_assigners(the_study)

    list_cur = list(result)
    df = pd.DataFrame(list_cur)
    if len(df) == 0:
        return df
    if 'contextuals' in df.columns:
        # fill nan with {}
        # TODO: Uniform may not have contextual.

        df['contextuals'] = df['contextuals'].apply(lambda x: {} if pd.isna(x) else x)
        df_normalized = pd.json_normalize(df['contextuals'].apply(flatten, args = (".",)))
        # Concatenate the flattened DataFrame with the original DataFrame
        df = pd.concat([df.drop('contextuals', axis=1), df_normalized], axis=1)

    df = df.rename(columns={
        "treatment$timestamp": "treatment.timestamp", 
        "outcome$timestamp": "outcome.timestamp"
        })
    

    df = df.sort_values(by=['treatment.timestamp', 'outcome.timestamp'])
    

    column_names_without_dot_values = [c.replace(".value", "") for c in df.columns]

    print(column_names_without_dot_values)
    column_mapping = dict(zip(df.columns, column_names_without_dot_values))

    # Rename the columns
    df = df.rename(columns=column_mapping)
        

    return df

@analysis_visualization_apis.route("/apis/create_dataset", methods = ["POST"])
def create_dataset():
    deployment = request.json['deployment'] if 'deployment' in request.json else None
    study = request.json['study'] if 'study' in request.json else None
    email = request.json['email'] if 'email' in request.json else None
    dataset_name = request.json['datasetName'] if 'datasetName' in request.json else None
    if deployment is None or study is None or dataset_name is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure deployment, study are provided."
        }), 400
    else:

        def is_valid_email(email):
            # Regular expression pattern for validating email addresses
            pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

            # Use the pattern to match the email address
            if re.match(pattern, email):
                return True
            else:
                return False
        try:
            df = create_df_from_mongo(study, deployment)

            if len(df) == 0:
                return status_code("DOWNLOADED_DATASET_EMPTY")

            the_deployment = DeploymentModel.get_one({"name": deployment})
            the_study = StudyModel.get_one({"name": study, "deploymentId": the_deployment['_id']})

            possible_variables = the_study['variables']


            variables = [v for v in list(df.columns) if v in possible_variables]
            versions = list(df['treatment'].unique())


            binary_data = pickle.dumps(df)
            # TODO: Check if name is already used
            document = {
                'dataset': binary_data,
                'deployment': deployment, 
                'name': dataset_name,
                'study': study, 
                'variables': variables,
                'versions': versions,
                'assigners': list(df['assigner'].unique()),
                'deploymentId': DeploymentModel.get_one({"name": deployment})['_id']
            }
            response = DatasetModel.create(document)

            # if EMAIL_NOTIFICATION and is_valid_email(email):
            #     subject = "Your Study datasets are ready for download."
            #     body = f'Your Study datasets are ready for download. Please visit this link: {ROOT_URL}/apis/analysis/downloadArrowDataset/{str(response.inserted_id)}'
            #     sender = EMAIL_USERNAME
            #     recipients = [request.get_json()['email']]
            #     password = EMAIL_PASSWORD
            #     msg = MIMEText(body)
            #     msg['Subject'] = subject
            #     msg['From'] = sender
            #     msg['To'] = ', '.join(recipients)
            #     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            #         smtp_server.login(sender, password)
            #         smtp_server.sendmail(sender, recipients, msg.as_string())

            return status_code("DOWNLOAD_DATASET_SUCCESSFUL")
        except Exception as e:
            # traceback
            import traceback
            print(traceback.format_exc())
            print(e)
            # if EMAIL_NOTIFICATION and is_valid_email(email):
            #     subject = "Sorry, downloading study datasets failed. please try again."
            #     body = subject
            #     sender = EMAIL_USERNAME
            #     recipients = [request.get_json()['email']]
            #     password = EMAIL_PASSWORD
            #     msg = MIMEText(body)
            #     msg['Subject'] = subject
            #     msg['From'] = sender
            #     msg['To'] = ', '.join(recipients)
            #     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            #         smtp_server.login(sender, password)
            #         smtp_server.sendmail(sender, recipients, msg.as_string())

            return status_code("DOWNLOAD_DATASET_FAILURE")