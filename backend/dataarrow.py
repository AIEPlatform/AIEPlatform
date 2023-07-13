

from flask import Flask, session
from flask_session import Session

from routes.user_interaction import user_interaction_apis
from routes.experiment_design import experiment_design_apis
from routes.analysis_visualization import analysis_visualization_apis
from routes.examples import examples_apis
from routes.integration import integration_apis

from routes.auth import auth_apis
from config import *
from credentials import *
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem" # Ideally we should use Redis or Memcached
Session(app)

# Currently still just use MOOClet APIs.

app.register_blueprint(user_interaction_apis)
app.register_blueprint(experiment_design_apis)
app.register_blueprint(analysis_visualization_apis)
app.register_blueprint(auth_apis)
app.register_blueprint(examples_apis)
app.register_blueprint(integration_apis)

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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=20110, debug=True, threaded=True)