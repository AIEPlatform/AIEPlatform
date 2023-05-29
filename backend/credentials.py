import os
from dotenv import load_dotenv
load_dotenv()
from flask import session
MONGO_DB_CONNECTION_STRING = os.getenv('MONGO_DB_CONNECTION_STRING')
PSQL_HOST = os.getenv('PSQL_HOST')
PSQL_PASSWORD = os.getenv('PSQL_PASSWORD')
PSQL_DATABASE = os.getenv('PSQL_DATABASE')
PSQL_USER = os.getenv('PSQL_USER')
PSQL_PORT = os.getenv('PSQL_PORT')
MOOCLET_TOKEN = os.getenv('MOOCLET_TOKEN')
MOOCLET_ENGINE_URL = os.getenv('MOOCLET_ENGINE_URL')
DEBUG = os.getenv('DEV_MODE') == 'True'
from pymongo import MongoClient

import psycopg2
conn = psycopg2.connect(
   database=PSQL_DATABASE, user=PSQL_USER, password=PSQL_PASSWORD, host=PSQL_HOST, 
        port=PSQL_PORT, 
        connect_timeout=3,
        keepalives=1,
        keepalives_idle=5,
        keepalives_interval=2,
        keepalives_count=2
)

client = MongoClient(MONGO_DB_CONNECTION_STRING)
db = client['adexacc']
Dataset = db['dataset']
Deployment = db['deployment']
Study = db['study']
MOOClet = db['mooclet']
MOOCletHistory = db['MOOCletHistory']
VariableValue = db['variableValue']
Interaction = db['interaction']
Variable = db['variable']


def check_if_loggedin():
    if 'access' in session and session['access'] is True or DEBUG:
        return True
    else:
        return False