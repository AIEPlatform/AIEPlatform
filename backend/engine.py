from flask import Flask, session
from flask_session import Session

from mooclet_datadownloader import mooclet_datadownloader_api
from dataarrow import dataarrow_apis
from auth import auth_apis
from bson import json_util
from dotenv import load_dotenv
import os
load_dotenv()
from credentials import *

MOOCLET_TOKEN = os.getenv('MOOCLET_TOKEN')
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem" # Ideally we should use Redis or Memcached
Session(app)

# Currently still just use MOOClet APIs.

app.register_blueprint(mooclet_datadownloader_api)
app.register_blueprint(dataarrow_apis)
app.register_blueprint(auth_apis)
@app.route("/apis/signUpMOOCletToken/<accessToken>", methods=["GET"])
def signUpMOOCletToken(accessToken):
    if accessToken == MOOCLET_TOKEN:
        session['access'] = True
    else:
        session['access'] = False
    return json_util.dumps({
        "status_code": 200, 
        "message": "Try again in the dashboard."
    }), 200


@app.route("/apis/checkLoginedOrNot", methods=["GET"])
def checkLoginedOrNot():
    if 'access' in session and session['access'] is True or DEBUG:
        return json_util.dumps({
            "status_code": 200
        }), 200
    else:
        return json_util.dumps({
            "status_code": 403
        }), 403
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=20110, debug=True, threaded=True)