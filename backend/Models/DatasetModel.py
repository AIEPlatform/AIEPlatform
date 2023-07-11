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
            updatedAt = datetime.datetime.now()
            email = get_username()
            dataset['owner'] = email
            dataset['createdAt'] = updatedAt
            dataset['updatedAt'] = updatedAt
            response = Dataset.insert_one(dataset, session=session)
            return response
        except:
            return None
        

    # delete by id
    @staticmethod
    def delete(datasetId, session = None):
        try:
            email = get_username()
            response = Dataset.delete_one({"_id": datasetId, "owner": email}, session=session)
            return response
        except:
            return None
        
    @staticmethod
    def delete_study_datasets(theDeployment, theStudy, session = None):
        try:
            email = get_username()
            response = Dataset.delete_many({"deploymentId": theDeployment['_id'], "study": theStudy['name'], "owner": email}, session=session)
            return response
        except:
            return None
        
    # update
    def update_one(datasetId, newDataset, session = None):
        try:
            # update the dataset field of theDataset, and refresh the updatedAt field.
            updatedAt = datetime.datetime.now()
            email = get_username()
            theDataset = Dataset.find_one({"_id": ObjectId(datasetId), "owner": email}, session=session)
            if theDataset is None:
                return 404 # not found or no permission.

            Dataset.update_one({"_id": ObjectId(datasetId)}, {"$set": {"dataset": pickle.dumps(newDataset), "updatedAt": updatedAt}}, session=session)
            return 200
        except Exception as e:
            print(e)
            return 500