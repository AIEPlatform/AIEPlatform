from credentials import *
import datetime


class LockModel:
    # get a lock
    @staticmethod
    def get_one(filter, projection = {}, session = None):
        return Lock.find_one(filter, projection, session=session)

    # get many
    @staticmethod
    def get_many(filter, projection = {}, session = None):
        return Lock.find(filter, projection, session=session)

    # create
    @staticmethod
    def create(lock, session = None):
        try:
            response = Lock.insert_one(lock, session=session)
            return response
        except:
            return None
        
    # delete
    def delete(lock, session = None):
        try:
            response = Lock.delete_one(lock, session=session)
            return response
        except:
            return None