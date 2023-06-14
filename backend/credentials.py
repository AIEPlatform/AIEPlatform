import os
from dotenv import load_dotenv
load_dotenv()
from flask import session
import pymongo

MONGO_DB_CONNECTION_STRING = os.getenv('MONGO_DB_CONNECTION_STRING')
DEBUG = os.getenv('DEV_MODE') == 'True'

EMAIL_USERNAME=os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD=os.getenv('EMAIL_PASSWORD')
ROOT_URL=os.getenv('ROOT_URL')

from pymongo import MongoClient
from pymongo.errors import PyMongoError


client = MongoClient(MONGO_DB_CONNECTION_STRING)
db = client['dataarrow']
Dataset = db['dataset']
Deployment = db['deployment']
Study = db['study']
MOOClet = db['mooclet']
MOOCletHistory = db['MOOCletHistory']
VariableValue = db['variableValue']
Interaction = db['interaction']
Variable = db['variable']
Lock = db['lock']
User = db['user']

TreatmentLog = db['treatmentLog']
RewardLog = db['rewardLog']

Deployment.create_index("name", unique=True)
Study.create_index([('name', pymongo.ASCENDING), ('deploymentId', pymongo.ASCENDING)], unique=True)
VariableValue.create_index([('variableName', pymongo.ASCENDING), ('user', pymongo.ASCENDING)])
VariableValue.create_index("variableName")

MOOClet.create_index([('name', pymongo.ASCENDING), ('studyId', pymongo.ASCENDING)], unique=True)

Interaction.create_index([('moocletId', pymongo.ASCENDING), ('user', pymongo.ASCENDING)])

Variable.create_index("name", unique=True)
Lock.create_index("moocletId", unique=True)
User.create_index("email", unique=True)




from bson.objectid import ObjectId
import pickle

def getDataset(datasetId):
    theDataset = Dataset.find_one({"_id": ObjectId(datasetId)}) # Only 
    df = pickle.loads(theDataset['dataset'])
    return df





def check_if_loggedin():
    if 'access' in session and session['access'] is True or DEBUG:
        return True
    else:
        return False