from config import *
from credentials import *


# Compatibility check.
# check if it has simulationSetting, if not, initialize it.
Study.update_many({"simulationSetting": {"$exists": False}}, {"$set": {"simulationSetting": {
            "baseReward": {},
            "contextualEffects": [],
            "numDays": 5
        }}})


# Change all simulation status to idle.
Study.update_many({}, {"$set": {"simulationStatus": "idle"}})
Deployment.update_many({"apiToken": {"$exists": False}}, {"$set": {"apiToken": None}})
Study.update_many({"status": {"$exists": False}}, {"$set": {"status": "running"}}) #currently only running and stopped.

Variable.update_many({"missingStrategy": {"$exists": False}}, {"$set": {"missingStrategy": "random"}}) #currently only running and stopped.

db['mooclet'].renameCollection('assigner')