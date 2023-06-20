from credentials import *
import datetime


class StudyModel:
    # get a study
    @staticmethod
    def get_one(filter, projection = {}, session = None):
        return Study.find_one(filter, projection, session=session)

    # get many
    @staticmethod
    def get_many(filter, projection = {}, session = None):
        return Study.find(filter, projection, session=session)

    # create
    @staticmethod
    def create(study, session = None):
        try:
            response = Study.insert_one(study, session=session)
            return response
        except:
            return None