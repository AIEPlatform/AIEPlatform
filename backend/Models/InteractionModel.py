from credentials import *
import datetime

from Models.AssignerModel import AssignerModel
class InteractionModel:
    @staticmethod
    def get_many(filter, public = False, session = None):
        if not public:
            email = get_username()
            filter['owner'] = email # TODO: Interaction doesn't have owner, but we still some protection.
        return Interaction.find(filter, session = session)
    # Get the last interaction for the given user at a study.
    @staticmethod
    def find_last_interaction(study, user, public = False, session = None):
        assigners = AssignerModel.find_study_assigners(study, public, session)

        # Find the latest interaction.
        the_interaction = Interaction.find_one({
            'user': user,
            'assignerId': {'$in': [assigner['_id'] for assigner in assigners]}
        })
        return the_interaction
    

    # Get all the interactions for a given study (for datadownloader).
    @staticmethod
    def get_interactions(study, session = None):
        try:
            theassigners = list(Assigner.find({"studyId": study['_id']}, {"_id": 1}))

            theassigners = [r['_id'] for r in theassigners]

            result = Interaction.aggregate([
                {
                    '$match': {
                        'assignerId': {"$in": theassigners}  # Specify the filter condition for collection1
                    }
                },
                {
                    '$lookup': {
                        'from': 'assigner',
                        'localField': 'assignerId',  # The field in collection1 to match
                        'foreignField': '_id',  # The field in collection2 to match
                        'as': 'joined_data',  # The name of the field in the output documents
                    }
                }, 
                {
                    '$unwind': '$joined_data'  # Unwind the 'joined_data' array
                }, 
                {
                    '$project': {"_id": 1, "user": 1, "policy": '$joined_data.policy', "assigner": '$joined_data.name', 'treatment': '$treatment.name', 'treatment$timestamp': '$timestamp', 'outcome': 1, 'where': 1, 'outcome$timestamp': '$rewardTimestamp', 'is_uniform': '$isUniform', 'contextuals': 1 }  # Project only the 'policy' field
                }
            ])

            return result
        except Exception as e:
            print(e)
            return None
    
    # Get the latest interaction for a given user at a study at a specific location.
    # TODO: We need to think about what happens if a user has been assigned to more than one Assigners. This's not supposed to happen, but what if a user was assigned to a assigner, and the assigner was deleted, and we have to assign them a different assigner?
    @staticmethod
    def get_latest_interaction_for_where(assignerId, user, where = None):
        try:
            if where is None:
                return Interaction.find_one({"user": user, "assignerId": assignerId}, sort=[("timestamp", -1)])
            else:
                print({"user": user, "assignerId": assignerId, "where": where})
                return Interaction.find_one({"user": user, "assignerId": assignerId, "where": where}, sort=[("timestamp", -1)])
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def get_interactions_for_where(assignerId, user, where = None):
        try:
            if where is None:
                return list(Interaction.find({"user": user, "assignerId": assignerId}))
            else:
                return list(Interaction.find({"user": user, "assignerId": assignerId, "where": where}))
        except Exception as e:
            print(e)
            return None


    # Get number of participants for an assigner.
    # TODO: should it be unique?
    @staticmethod
    def get_num_participants_for_assigner(assignerId):
        try:
            return len(list(Interaction.find({"assignerId": assignerId})))
        except:
            return 0
        
    @staticmethod
    def get_num_participants_for_assigner_individual(assignerId, user):
        try:
            return len(list(Interaction.find({"assignerId": assignerId, "user": user})))
        except:
            return 0

    # Insert a new model
    @staticmethod
    def insert_one(the_interaction, session = None):
        Interaction.insert_one(the_interaction)


    # Append a reward to this interaction
    @staticmethod
    def append_reward(interactionId, reward, session=None):
        try:
            current_time = datetime.datetime.now()
            Interaction.update_one({'_id': interactionId}, {'$set': {'outcome': reward, 'rewardTimestamp': current_time}})
            return 200
        except:
            return 500
        

    # Find all unused interactions for a given assigner
    @staticmethod
    def find_earliest_unused(assignerId, user = None, session = None):
        earliest_unused = None
        if user is None:
            earliest_unused = Interaction.find_one(
                            {"assignerId": assignerId, "outcome": {"$ne": None}, "used": {"$ne": True}}
                            ) # TODO: Shall we exclute those from uniform (I don't think so?)
        else:
            earliest_unused = Interaction.find_one(
                            {"assignerId": assignerId, "user": user, "outcome": {"$ne": None}, "used": {"$ne": True}}
                            ) # TODO: Shall we exclute those from uniform (I don't think so?)
        return earliest_unused
    

    # use_unused_interactions
    @staticmethod
    def use_unused_interactions(assignerId, user = None, session = None):
        if user is None:
            interactions_for_posterior = list(Interaction.find(
                {"assignerId": assignerId, "outcome": {"$ne": None}, "used": {"$ne": True}}, session=session
                )) # TODO: Need to somehow tag interactions as having been used for posterior already or by time.
            
            Interaction.update_many(
                {"assignerId": assignerId, "outcome": {"$ne": None}, "used": {"$ne": True}}, {"$set": {"used": True}}, session=session
                )
            
            # TODO: Verify that when this function is called, there should never be overlapping in two different calls.
            # get ids of interactions
            # interaction_ids = [interaction['_id'] for interaction in interactions_for_posterior]
            # # write into a text: one line is one id
            # with open('interactions_for_posterior.txt', 'a') as f:
            #     for item in interaction_ids:
            #         f.write("%s\n" % item)
            return interactions_for_posterior
        else:
            interactions_for_posterior = list(Interaction.find(
                {"assignerId": assignerId, "user": user, "outcome": {"$ne": None}, "used": {"$ne": True}}, session=session
                )) # TODO: Need to somehow tag interactions as having been used for posterior already or by time.
            
            Interaction.update_many(
                {"assignerId": assignerId, "user": user, "outcome": {"$ne": None}, "used": {"$ne": True}}, {"$set": {"used": True}}, session=session
                )
        
            return interactions_for_posterior
    
    # get assigner number of feedback
    @staticmethod
    def get_assigner_num_feedback(assignerId, session = None):
        return Interaction.count_documents({"assignerId": assignerId, "outcome": {"$ne": None}}, session=session)
    







    # return a list of all NON-NAN outcome for the given version from the given assigner.
    @staticmethod
    def get_assigner_outcome_by_version(assignerId, version, session = None):
        try:
            result = Interaction.aggregate([
                {
                    '$match': {
                        'assignerId': assignerId,  # Specify the filter condition for collection1
                        'outcome': {'$ne': None},
                        'treatment': version
                    }
                },
                {
                    '$project': {"outcome": 1}  # Project only the 'policy' field
                }
            ])
            #TODO: INCREASE THE EFFICIENCY
            result = [r['outcome'] for r in result]
            return result
        except Exception as e:
            print(e)
            return None
        
    # return a list of all NON-NAN outcome for the given version from the given assignerId.
    @staticmethod
    def get_study_outcome_by_version(studyId, version, session = None):
        try:
            theAssigners = list(Assigner.find({"studyId": studyId}, {"_id": 1}))

            theAssigners = [r['_id'] for r in theAssigners]

            result = Interaction.aggregate([
                {
                    '$match': {
                        'assignerId': {"$in": theAssigners},  # Specify the filter condition for collection1
                        'outcome': {'$ne': None},
                        'treatment': version
                    }
                },
                {
                    '$project': {"outcome": 1}  # Project only the 'policy' field
                }
            ])
            result = [r['outcome'] for r in result]
            return result
        except Exception as e:
            print(e)
            return None


    @staticmethod
    def auto_zero(filter_query, update_query, session = None):
        try:
            Interaction.update_many(filter_query, update_query, session=session)
            return 200
        except:
            return 500