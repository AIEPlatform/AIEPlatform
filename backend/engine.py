from flask import Flask
from flask_pymongo import PyMongo
from mooclet import mooclet_apis
from mooclet_datadownloader import mooclet_datadownloader_api


app = Flask(__name__)

# Currently still just use MOOClet APIs.

app.register_blueprint(mooclet_apis)
app.register_blueprint(mooclet_datadownloader_api)
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=20110, debug=True, threaded=True)