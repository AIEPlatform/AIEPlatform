from credentials import *
import datetime


class DatasetModel:
    # get a Dataset
    @staticmethod
    def get_one(filter, projection = {}, session = None):
        return Dataset.find_one(filter, projection, session=session)

    # get many
    @staticmethod
    def get_many(filter, projection = {}, session = None):
        return Dataset.find(filter, projection, session=session)

    # create
    @staticmethod
    def create(dataset, session = None):
        try:
            response = Dataset.insert_one(dataset, session=session)
            return response
        except:
            return None