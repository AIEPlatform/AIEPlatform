from flask import Flask, session
from flask import Blueprint, session
from flask import request
from bson import json_util
from helpers import *
from credentials import *
from flask_bcrypt import Bcrypt
app = Flask(__name__)
bcrypt = Bcrypt(app)
auth_apis = Blueprint('auth_apis', __name__)

# Authe logis are definied in this py file.
@auth_apis.route("/apis/auth/login", methods=["POST"])
def login():
    if 'user' in session:
        return json_util.dumps({"status": 200, "message": "Already logged in. If you want to login as a different user, logout first."})
    

    #https://stackoverflow.com/questions/63010231/password-encryption-in-flask
    email = request.json['email'] if 'email' in request.json else None
    password = request.json['password'] if 'password' in request.json else None
    if email is None or password is None:
        return json_util.dumps({"status": 400, "message": "Email or password not provided"})
    
    # TODO: Check password complexity.
    pw_hash = bcrypt.generate_password_hash(password)
    the_user = User.find_one({"email": email})
    if the_user is None:
        return json_util.dumps({"status": 400, "message": "Email not found."})
    if not bcrypt.check_password_hash(the_user['password'], password):
        return json_util.dumps({"status": 400, "message": "Password incorrect."})
    session['user'] = the_user
    return json_util.dumps({"status": 200, "message": "Logged in successfully."})


# Test it 
@auth_apis.route("/apis/auth/logout", methods=["GET"])
def logout():
    if 'user' in session:
        session.pop('user')
    return json_util.dumps({"status": 200, "message": "Logged out successfully."})

@auth_apis.route("/apis/auth/signup", methods=["POST"])
def signup():
    if 'user' in session:
        return json_util.dumps({"status": 200, "message": "Already logged in. If you want to signup as a different user, logout first."})
    
    email = request.json['email'] if 'email' in request.json else None
    password = request.json['password'] if 'password' in request.json else None
    firstName = request.json['firstName'] if 'firstName' in request.json else None
    lastName = request.json['lastName'] if 'lastName' in request.json else None
    if email is None or password is None or firstName is None or lastName is None:
        return json_util.dumps({"status": 400, "message": "Email, password, firstName, or lastName not provided"}), 400
    
    # check if email already exists.
    the_user = User.find_one({"email": email})
    print(the_user)
    if the_user is not None:
        return json_util.dumps({"status": 400, "message": "Email already exists."}), 400
    
    password = bcrypt.generate_password_hash(password)
    User.insert_one({"firstName": firstName, "lastName": lastName, "email": email, "password": password})
    return json_util.dumps({"status": 200, "message": "Signed up successfully."})


# Get the current user.
@auth_apis.route("/apis/auth/currentUser", methods=["GET"])
def current_user():
    if 'user' not in session:
        return json_util.dumps({"status": 400, "message": "Not logged in.", "user": None})
    return json_util.dumps({"status": 200, "message": "Logged in.", "user": session['user']})



# Change password.
@auth_apis.route("/apis/auth/changePassword", methods=["PUT"])
def change_password():
    try:
        if 'user' not in session:
            return json_util.dumps({"status": 400, "message": "Not logged in.", "user": None}), 400
        email = session['user']['email']
        the_user = User.find_one({"email": email})
        if the_user is None:
            return json_util.dumps({"status": 400, "message": "Email not found."})
        old_password = request.json['currentPassword'] if 'currentPassword' in request.json else None
        new_password = request.json['newPassword'] if 'newPassword' in request.json else None
        if old_password is None or new_password is None:
            return json_util.dumps({"status": 400, "message": "Old password or new password not provided"}), 400
        if not bcrypt.check_password_hash(the_user['password'], old_password):
            return json_util.dumps({"status": 400, "message": "Old password incorrect."}), 400
        new_password = bcrypt.generate_password_hash(new_password)

        # Update the password
        User.update_one({"email": email}, {"$set": {"password": new_password}})
        return json_util.dumps({"status": 200, "message": "Password changed successfully."})
    except Exception as e:
        print(e)
        return json_util.dumps({"status": 500, "message": "Something went wrong."}), 500