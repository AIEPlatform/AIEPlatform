from credentials import *
from flask import Blueprint, session
from flask import request
from bson import json_util
from bson.objectid import ObjectId
from helpers import *
from Models.DeploymentModel import DeploymentModel
from Models.DatasetModel import DatasetModel
from errors import *
import pandas as pd
import pickle
from bson.objectid import ObjectId
from flask import send_file, make_response
from Analysis.basic_reward_summary_table import basic_reward_summary_table
from Analysis.AverageRewardByTime import AverageRewardByTime

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


@analysis_visualization_apis.route("/apis/analysis/basic_reward_summary_table", methods = ["POST"])
def basic_reward_summary_table_api():
    theDatasetId = request.json['theDatasetId'] if 'theDatasetId' in request.json else None # This is the id.
    
    selected_variables = request.json['selectedVariables'] if 'selectedVariables' in request.json else []

    selected_assigners = request.json['selectedAssigners'] if 'selectedAssigners' in request.json else []
 
    if theDatasetId is None:
        return json_util.dumps({
            "status_code": 400,
            "message": "Please make sure the_study_basic_info, selected_variables are provided."
        }), 400
    else:
        df = getDataset(theDatasetId)
        result_df = basic_reward_summary_table(df, selected_variables, selected_assigners)
        return json_util.dumps({
            "status_code": 200,
            "message": "Table returned.",
            "result": {
                "columns": list(result_df.columns), 
                "rows": [tuple(r) for r in result_df.to_numpy()]
            }
        }), 200


@analysis_visualization_apis.route("/apis/analysis/AverageRewardByTime", methods = ["POST"])
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
    