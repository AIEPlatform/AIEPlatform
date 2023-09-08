from credentials import *
import datetime
import traceback

class LockModel:
    # get a lock
    @staticmethod
    def get_one(filter, projection = {}, session = None):
        return Lock.find_one(filter, session=session)

    # get many
    @staticmethod
    def get_many(filter, projection = {}, session = None):
        return Lock.find(filter, session=session)

    # create
    @staticmethod
    def create(lock, session = None):
        locks = list(Lock.find({}))
        try:
            response = Lock.insert_one(lock, session=session)
            return response
        except Exception as e:
            print("Lock Inserting Error Report Start")
            print(e)
            print(traceback.format_exc())
            print("Lock Inserting Error Report End")
            return None
        
    # delete
    def delete(lock, session = None):
        try:
            response = Lock.delete_one(lock, session=session)
            return response
        except:
            return None