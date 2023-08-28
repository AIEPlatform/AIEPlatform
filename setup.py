import os
import json

from pymongo import MongoClient
# check if backend/config.py exists. If not, make a new one.
if not os.path.isfile('backend/config.json'):
    # create a new config.py file
    with open('backend/config.json', 'w') as f:
        # write an empty json object
        empty_config = {}
        json.dump(empty_config, f, indent=4)

# the config.py has a dictionary, load it.
required_variables = [
    "MONGO_DB_CONNECTION_STRING",
    "DB_NAME",
    "DEV_MODE"
]

def handle(variable, config):
    if variable not in config:
        config[variable] = None
        print("Please enter the value for " + variable + ":")
        config[variable] = input()
    else:
        # ask if they want to update the value or not.
        print("Do you want to update the value for " + variable + "? (y/n)")
        answer = input()
        if answer == "y":
            print("Please enter the value for " + variable + ":")
            config[variable] = input()
        else:
            print("Skipping " + variable + "...")

with open('backend/config.json', 'r') as f:
    config = json.load(f)
    if "OPEN_AI_KEY" not in config: config["OPEN_AI_KEY"] = None
    for variable in ["MONGO_DB_CONNECTION_STRING", "DB_NAME"]:
        handle(variable, config)

    # check if connection is successful.
    try:
        print("checking connection...")
        client = MongoClient(config['MONGO_DB_CONNECTION_STRING'])
        db = client[config['DB_NAME']]
        # check if the connection is successful.
        db.list_collection_names()
    except Exception as e:
        print("Error: " + str(e))
        print("Connection fails. Please re-run the setup.py with the correct credentials.")
        exit(1)

    for variable in ["OPEN_AI_KEY"]:
        handle(variable, config)
    # ask if they want email feature.
    
    if 'DEV_MODE' not in config: config['DEV_MODE'] = True

    print("Is this instance for dev or not? (y/n)")
    answer = input()
    if answer == "y":
        config['DEV_MODE'] = True
    else:
        config['DEV_MODE'] = False

    print("Set up complete.")

    

# write the config back to the file.
with open('backend/config.json', 'w') as f:
    json.dump(config, f, indent=4)