from credentials import *
import datetime


class DatasetModel:
    # get a Dataset
    @staticmethod
    def get_one(filter, projection = {}, public = False, session = None):
        if not public:
            email = get_username()
            filter['owner'] = email
        return Dataset.find_one(filter, projection, session=session)

    # get many
    @staticmethod
    def get_many(filter, projection = {}, public = False, session = None):
        if not public:
            email = get_username()
            filter['owner'] = email

        print(email)
        return Dataset.find(filter, projection, session=session)

    # create
    @staticmethod
    def create(dataset, session = None):
        try:
            email = get_username()
            dataset['owner'] = email
            response = Dataset.insert_one(dataset, session=session)
            return response
        except:
            return None
        

    # delete by id
    @staticmethod
    def delete(datasetId, session = None):
        print("dfghdfhdfhfdh")
        try:
            email = get_username()
            response = Dataset.delete_one({"_id": datasetId, "owner": email}, session=session)
            return response
        except:
            return None