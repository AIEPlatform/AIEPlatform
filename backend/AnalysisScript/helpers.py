import os
from dotenv import load_dotenv
load_dotenv()
MONGO_DB_CONNECTION_STRING = os.getenv('MONGO_DB_CONNECTION_STRING')
PSQL_HOST = os.getenv('PSQL_HOST')
PSQL_PASSWORD = os.getenv('PSQL_PASSWORD')
PSQL_DATABASE = os.getenv('PSQL_DATABASE')
PSQL_USER = os.getenv('PSQL_USER')
PSQL_PORT = os.getenv('PSQL_PORT')
MOOCLET_TOKEN = os.getenv('MOOCLET_TOKEN')
MOOCLET_ENGINE_URL = os.getenv('MOOCLET_ENGINE_URL')

import pymongo
from pymongo import MongoClient

import pandas as pd

client = MongoClient(MONGO_DB_CONNECTION_STRING)
db = client['mooclet']
Dataset = db['dataset']

def get_dataset(dataset_name):
    dataset = Dataset.find_one({'datasetDescription': dataset_name})
    return pd.DataFrame(dataset['dataset'])