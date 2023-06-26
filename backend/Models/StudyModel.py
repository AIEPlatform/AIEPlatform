from credentials import *
import datetime
from Models.DeploymentModel import DeploymentModel


class StudyModel:
    # get a study
    @staticmethod
    def get_one(filter, projection = {}, public = False, session = None):
        if not public:
            email = get_username()
            deploymentIds = list(DeploymentModel.get_many({"owner": email}, {"_id": 1}))
            deploymentIds = [r['_id'] for r in deploymentIds]
            filter['deploymentId'] = {"$in": deploymentIds}
        return Study.find_one(filter, projection, session=session)

    # get many
    @staticmethod
    def get_many(filter, projection = {}, public = False, session = None):
        if not public:
            email = get_username()
            deploymentIds = list(DeploymentModel.get_many({"owner": email}, {"_id": 1}))
            deploymentIds = [r['_id'] for r in deploymentIds]
            filter['deploymentId'] = {"$in": deploymentIds}
        return Study.find(filter, projection, session=session)

    # create
    @staticmethod
    def create(study, session = None):
        try:
            response = Study.insert_one(study, session=session)
            return response
        except:
            return None