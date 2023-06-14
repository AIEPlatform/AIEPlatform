from credentials import *
import datetime


class DeploymentModel:
    # get a Deployment
    @staticmethod
    def get_one(filter, projection = {}, session = None):
        return Deployment.find_one(filter, projection, session=session)

    # get many
    @staticmethod
    def get_many(filter, projection = {}, session = None):
        return Deployment.find(filter, projection, session=session)

    # create
    @staticmethod
    def create(deployment, session = None):
        try:
            response = Deployment.insert_one(deployment, session=session)
            return response
        except:
            return None