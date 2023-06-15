from credentials import *
import datetime


class VariableModel:
    # get a Variable
    @staticmethod
    def get_one(filter, projection = {}, session = None):
        email = get_username()
        filter['owner'] = email
        return Variable.find_one(filter, projection, session=session)

    # get many
    @staticmethod
    def get_many(filter, projection = {}, session = None):
        email = get_username()
        filter['owner'] = email
        return Variable.find(filter, projection, session=session)

    # create
    @staticmethod
    def create(variable, session = None):
        try:
            response = Variable.insert_one(variable)
            return response
        except Exception as e:
            print(e)
            return None