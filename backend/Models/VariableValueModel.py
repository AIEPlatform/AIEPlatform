from credentials import *
class VariableValueModel:
    # Static methods:
    # Get the latest value for each of the given variables for the given user.
    @staticmethod
    def get_latest_variable_values(variableNames, user, session = None):
        column_name = 'variableName'
        array_list = variableNames  # Example array list

        # Aggregation pipeline to filter and keep the last occurrence
        pipeline = [
            {
                '$match': {
                    column_name: {'$in': array_list}, 
                    'user': user
                }
            },
            {
                '$sort': {
                    'timestamp': 1       # Sort descending by _id (to get the last occurrence)
                }
            },
            {
                '$group': {
                    '_id': '$' + column_name,
                    'lastDocument': {'$last': '$$ROOT'}
                }
            },
            {
                '$replaceRoot': {'newRoot': '$lastDocument'}
            }
        ]

        # Execute the aggregation pipeline
        result = list(VariableValue.aggregate(pipeline))

        return result
    
    # Insert a new variable value for the given user.
    # TODO: error handling.
    @staticmethod
    def insert_variable_value(variable, session = None):
        try:
            VariableValue.insert_one(variable, session = session)
            return 200
        except Exception as e:
            print(e)
            return 500
