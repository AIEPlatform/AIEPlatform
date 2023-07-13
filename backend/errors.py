from bson import json_util
status_codes = {
    "DOWNLOADED_DATASET_EMPTY": {
        "status": 400, 
        "code": "4401", 
        "message": "The downloaded dataset is empty. It's not saved to the database."
    }, 

    "DOWNLOAD_DATASET_FAILURE": {
        "status": 500, 
        "code": "5401", 
        "message": "Sorry, downloading mooclet datasets failed. please try again."
    }, 
    "DOWNLOAD_DATASET_SUCCESSFUL": {
        "status": 200, 
        "code": "200", 
        "message": "Your dataset is downloaded succesfully. Your next step will be at the analysis page, where you can see data analysis and visulizations. You can also choose to modify the dataset and re-upload it."
    }, 
    "UPLOAD_LOCAL_MODIFICATION_SUCCESSFUL": {
        "status": 200, 
        "code": "200", 
        "message": "Your local modification has been applied."
    }, 
    "DEFAULT_SERVER_ERROR": {
        "status": 500, 
        "code": "500", 
        "message": "Something is wrong."
    }
}


def status_code(code, others = {}):
    return json_util.dumps({
        "status": status_codes[code]['status'],
        "code": status_codes[code]['code'],
        "message": status_codes[code]['message']
    }), status_codes[code]['status']


class StudyNotFound(Exception):
    pass

class DeploymentNotFound(Exception):
    pass

class InvalidDeploymentToken(Exception):
    pass