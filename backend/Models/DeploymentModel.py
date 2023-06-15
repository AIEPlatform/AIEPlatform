from credentials import *
import datetime


class DeploymentModel:
    # get a Deployment
    @staticmethod
    def get_one(filter, projection = {}, dbSession = None):
        email = get_username()
        filter['owner'] = email
        return Deployment.find_one(filter, projection, session=dbSession)

    # get many
    @staticmethod
    def get_many(filter, projection = {}, dbSession = None):
        email = get_username()
        filter['owner'] = email
        return Deployment.find(filter, projection, session=dbSession)

    # create
    @staticmethod
    def create(deployment, dbSession = None):
        try:
            if 'owner' not in deployment:
                deployment['owner'] = get_username()
            response = Deployment.insert_one(deployment, session=dbSession)
            return response
        except:
            return None