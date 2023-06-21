from credentials import *
import datetime
class MOOCletModel:
    # Update policy parameters
    @staticmethod
    def update_policy_parameters(moocletId, toUpdate, session = None):
        try:
            MOOClet.update_one({"_id": moocletId}, {"$set": toUpdate}, session=session)
            return 200
        except Exception as e:
            print(e)
            return 500

    # find mooclets of a specific study
    @staticmethod
    def find_study_mooclets(study, session):
        mooclets = list(MOOClet.find(
            {
                'studyId': study['_id'],
            }, {'_id': 1}
        ))
        return mooclets
    

    # find a mooclet by filter
    def find_mooclet(filter, projection = {}, session = None):
        return MOOClet.find_one(filter, projection, session=session)
    
    # find mooclets by filter
    def find_mooclets(filter, projection = {}, session = None):
        return MOOClet.find(filter, projection, session=session)
    

    # Insert a mooclet object
    def create(mooclet, session = None):
        try:
            response = MOOClet.insert_one(mooclet, session=session)
            return response
        except:
            return 500
        

    # update mooclet
    def update(filter, toUpdate, session = None):
        MOOClet.update_one(filter,toUpdate, session=session)
