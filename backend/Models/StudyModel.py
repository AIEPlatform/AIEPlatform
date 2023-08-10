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
    def get_many(filter, projection = {}, public = False, session = None, showDeploymentName = False):
        if not public:
            email = get_username()
            deploymentIds = list(DeploymentModel.get_many({"owner": email}, {"_id": 1}))
            deploymentIds = [r['_id'] for r in deploymentIds]
            filter['deploymentId'] = {"$in": deploymentIds}

        if not showDeploymentName:
            return Study.find(filter, projection, session=session)
        
        else:
            pipeline = [
                {
                    "$match": filter  # Add the filter criteria to the $match stage
                },
                {
                    "$lookup": {
                        "from": "deployment",
                        "localField": "deploymentId",
                        "foreignField": "_id",
                        "as": "deployment"
                    }
                },
                {
                    "$unwind": "$deployment"  # Since the join could result in an array, unwind it to get individual documents
                }
            ] 
            result = Study.aggregate(pipeline)
            return result
    

    def get_deployment_studies(deploymentId, session = None):
        return Study.find({"deploymentId": deploymentId}, session=session)

    # create
    @staticmethod
    def create(study, session = None):
        try:
            response = Study.insert_one(study, session=session)
            return response
        except:
            return None
        
    # delete by id
    @staticmethod
    def delete_one_by_id(studyId, session = None):
        try:
            response = Study.delete_one({"_id": studyId}, session=session)
            return response
        except:
            return None
