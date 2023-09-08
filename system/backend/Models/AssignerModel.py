from credentials import *
import datetime
class AssignerModel:
    # Update policy parameters
    @staticmethod
    def update_policy_parameters(assignerId, toUpdate, session = None):
        try:
            # Write into History!!!
            currentAssigner = Assigner.find_one({"_id": assignerId}, session=session)
            History.insert_one({
                "assignerId": assignerId,
                "timestamp": datetime.datetime.now(),
                "parameters": currentAssigner['parameters']
            }, session=session)
            Assigner.update_one({"_id": assignerId}, {"$set": toUpdate}, session=session)
            return 200
        except Exception as e:
            print(e)
            return 500

    # find assigners of a specific study
    @staticmethod
    def find_study_assigners(study, public = False, session = None):
        assigners = list(Assigner.find(
            {
                'studyId': study['_id'],
            }, {'_id': 1}
        ))
        return assigners
    

    # find a assigner by filter
    def find_assigner(filter, projection = {}, session = None):
        return Assigner.find_one(filter, projection, session=session)
    
    # find assigners by filter
    def find_assigners(filter, projection = {}, session = None):
        return Assigner.find(filter, projection, session=session)
    

    # Insert a assigner object
    def create(assigner, session = None):
        try:
            response = Assigner.insert_one(assigner, session=session)
            return response
        except:
            return 500
        

    # update assigner
    def update(filter, toUpdate, session = None):
        Assigner.update_one(filter,toUpdate, session=session)


    def delete_study_assigners(studyId, session = None):
        try:
            response = Assigner.delete_many({"studyId": studyId}, session=session)
            return response
        except:
            return None
