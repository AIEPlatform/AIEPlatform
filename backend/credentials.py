import os
from config import *
from flask import session
import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from bson.objectid import ObjectId
import pickle


client = MongoClient(MONGO_DB_CONNECTION_STRING)
db = client[DB_NAME]
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
History = db['history']

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


MOOCletIndividualLevelInformation = db['MOOCletIndividualLevelInformation']

def getDataset(datasetId):
    theDataset = Dataset.find_one({"_id": ObjectId(datasetId)}) # Only 
    df = pickle.loads(theDataset['dataset'])
    return df

def check_if_loggedin():
    if 'access' in session and session['access'] is True or DEV_MODE:
        return True
    else:
        return False
    
def get_username():
    if 'user' in session:
        return session['user']['email']
    elif DEV_MODE:
        return "chenpan"
    else:
        return None