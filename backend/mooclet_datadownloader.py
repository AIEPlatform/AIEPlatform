from flask import Blueprint
from bson import json_util
from flask import request
from io import BytesIO
from flask import send_file, make_response
import pandas as pd
import pymongo
from pymongo import MongoClient
import os
import requests
import json
import math
import numpy as np
from credentials import *
import uuid
from psycopg2.extensions import AsIs
import pickle

# SELECT * FROM pg_stat_activity;

# SELECT 
#     pg_terminate_backend(pid) 
# FROM 
#     pg_stat_activity 
# WHERE client_addr = '99.227.240.244';


client = MongoClient(MONGO_DB_CONNECTION_STRING)
db = client['mooclet']
Dataset = db['dataset']

mooclet_datadownloader_api = Blueprint('mooclet_datadownloader_api', __name__)


def data_downloader_local_new(mooclet_name, reward_variable_name):
    # GET DATA
    cursor = conn.cursor()
    unique_id = str(uuid.uuid4()).replace("-", "_")
    #TODO: Think about concurrency! Use unique id for now.
    reward_values_view = AsIs(f'reward_values_{unique_id}')
    context_values_view = AsIs(f'context_values_{unique_id}')
    arm_assignments_view = AsIs(f'arm_assignments_{unique_id}')
    arm_reward_merged_view = AsIs(f'arm_reward_merged_{unique_id}')
    arm_reward_merged_max_view = AsIs(f'arm_reward_merged_max_{unique_id}')
    contexts_merged_view = AsIs(f'contexts_merged_{unique_id}')
    contexts_merged_max_view = AsIs(f'contexts_merged_max_{unique_id}')
    try:
        print(f'MOOClet name: {mooclet_name}')
        print(f'Reward variable Name: {reward_variable_name}')

        #Reserved variables are variables that are not reward or contextual variables. We don't want them in the dataset.
        reserved_variable_names = ['UR_or_TSCONTEXTUAL', 'coef_draw', 'precesion_draw', 'version', '']
        cursor.execute("SELECT array_agg(distinct(id)) from engine_variable where name = ANY(%s);", [reserved_variable_names])
        reserved_variable_ids = cursor.fetchall()[0][0]

        # get mooclet id
        cursor.execute("select id from engine_mooclet where name = %s;", [mooclet_name]);
        mooclet_id = cursor.fetchone()[0]
        print(f'MOOClet id: {mooclet_id}')
        # get reward variable id
        cursor.execute("select id from engine_variable where name = %s;", [reward_variable_name]);
        reward_variable_id = cursor.fetchone()[0]
        print(f'Reward variable id: {reward_variable_id}')

        # get the variable id used for version (arm assignments)
        cursor.execute("select id from engine_variable where name = 'version';");
        version_id = cursor.fetchone()[0]
        print(f'Version id: {version_id}')   



        # get all reward values
        cursor.execute("""
            CREATE TEMPORARY VIEW %s AS
            SELECT * FROM
            engine_value WHERE variable_id = %s AND mooclet_id = %s;
            """, [reward_values_view, reward_variable_id, mooclet_id])
        
         # get all context values
        cursor.execute("""
            CREATE TEMPORARY VIEW %s AS
            SELECT * FROM
            engine_value WHERE variable_id != %s AND mooclet_id = %s and version_id is null AND variable_id != ALL(%s);
            """, [context_values_view, reward_variable_id, mooclet_id, reserved_variable_ids])

        # Get all arm assignments (as a base to which we are appending reward & contextual based on some condition)
        cursor.execute("""
            CREATE TEMPORARY VIEW %s AS
            SELECT * FROM
            engine_value WHERE variable_id = %s AND mooclet_id = %s;
            """, [arm_assignments_view, version_id, mooclet_id])
        
        # First, merge arm assignments with rewards after it.
        cursor.execute("""
            CREATE TEMPORARY VIEW %s AS
            SELECT aa.id as assignment_id, aa.learner_id, aa.policy_id, aa.text AS arm, r.variable_id as reward_id, r.value as reward_value, r.timestamp as reward_time, aa.timestamp as arm_time, r.id as reward_value_id
            FROM %s aa LEFT JOIN %s r ON aa.learner_id = r.learner_id and aa.timestamp < r.timestamp;
        """, [arm_reward_merged_view, arm_assignments_view, reward_values_view])
        # Second, find earliest rewards for each LEFT join pair.
        cursor.execute("""
            CREATE TEMPORARY VIEW %s AS
            WITH arm_reward_merged_with_rank AS (
            SELECT
                *,
                ROW_NUMBER() OVER(PARTITION BY assignment_id ORDER BY reward_time) AS row_number
                FROM %s
            )
            SELECT
                *, COALESCE(arm_reward_merged_with_rank.reward_time, arm_reward_merged_with_rank.arm_time) AS time_to_find_contexts
                FROM arm_reward_merged_with_rank
                WHERE row_number = 1;
        """, [arm_reward_merged_max_view, arm_reward_merged_view])
        # Manually add a column called time_to_find_contexts to use to find contexts.

        cursor.execute("""
            CREATE TEMPORARY VIEW %s AS
            SELECT ar.assignment_id, ar.learner_id, ar.policy_id, ar.arm, ar.reward_value_id, ar.reward_id, ar.reward_value, ar.reward_time, ar.arm_time, ar.row_number, ar.time_to_find_contexts, c.id as context_value_id, c.value as context_value, c.variable_id as context_variable_id, c.timestamp as context_time, CASE WHEN c.text = 'Init Context' THEN True ELSE False END AS context_imputed
            FROM %s ar LEFT JOIN %s c ON ar.learner_id = c.learner_id and c.timestamp < ar.time_to_find_contexts;
        """, [contexts_merged_view, arm_reward_merged_max_view, context_values_view])

        #TODO: check if above makes sense, because now we may use reward time or assignment time.

        # Second, find largest contexts for each LEFT join pair.
        
        cursor.execute("""
            CREATE TEMPORARY VIEW %s AS
            WITH arm_reward_contexts_merged_with_rank AS (
            SELECT
                *,
                ROW_NUMBER() OVER(PARTITION BY (assignment_id, context_variable_id) ORDER BY context_time DESC) AS row_number2
                FROM %s
            )
            SELECT
                *
                FROM arm_reward_contexts_merged_with_rank
                WHERE row_number2 = 1;
        """, [contexts_merged_max_view, contexts_merged_view])



        # Now we have everything, but we still need to map IDs with Names.
        cursor.execute("""
            SELECT t0.assignment_id, t0.learner_id, t3.name as policy_name, t0.arm, t0.arm_time, t0.reward_value_id, t1.name as reward_name, t0.reward_value, t0.reward_time, t0.context_value_id, t2.name as context_name, t0.context_value, t0.context_time, t0.context_imputed from %s t0 LEFT JOIN engine_variable t1 on (t0.reward_id = t1.id) LEFT JOIN engine_variable t2 on (t0.context_variable_id = t2.id) LEFT JOIN engine_policy t3 on (t0.policy_id = t3.id);
        """, [contexts_merged_max_view])

        result = cursor.fetchall()



        # TODO: Do Pivot in SQL!
        
        df = pd.DataFrame(data = result, columns= [i[0] for i in cursor.description])
        contextual_values = df['context_name'].dropna().unique()
        right_order = []
        for contextual_value in contextual_values:
            right_order.append(f'context_value_id_{contextual_value}')
            right_order.append(f'context_value_{contextual_value}')
            right_order.append(f'context_time_{contextual_value}')
            right_order.append(f'context_imputed_{contextual_value}')
        pivot_df = df.pivot(index=['assignment_id', 'learner_id', 'policy_name', 'arm', 'arm_time', 'reward_value_id', 'reward_name', 'reward_value', 'reward_time'],
                            columns=['context_name'],
                            values=['context_value_id', 'context_value', 'context_time', 'context_imputed'])
        

        # Flatten the column names
        pivot_df.columns = [f'{col[0]}_{col[1]}' for col in pivot_df.columns]

        pivot_df.replace({np.nan: None}, inplace = True)
        # Reset the index
        # print(right_order)
        # print(pivot_df.columns)
        pivot_df = pivot_df.drop(['reward_value_id_nan', 'context_value_id_nan', 'context_value_nan','context_time_nan', 'context_imputed_nan', 'assignment_id'], axis=1, errors='ignore')
        pivot_df = pivot_df.reset_index()
        pivot_df = pivot_df.rename(columns={'policy_name': 'policy', 'reward_value': 'reward'})

        df = pivot_df

        mask = df['reward_value_id'].duplicated(keep='last')

        # Set reward_name, reward, and reward_time to None for non-last occurrences
        df.loc[mask, ['reward_name', 'reward', 'reward_time']] = np.nan
        cursor.execute(
            """
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            """, [reward_values_view, context_values_view, arm_assignments_view, arm_reward_merged_view, arm_reward_merged_max_view, contexts_merged_view, contexts_merged_max_view]
        )
        cursor.close()

        # df = df.drop(['assignment_id'], axis=1, errors='ignore')


        columns = df.columns.tolist()
        other_columns = [col for col in columns if col not in right_order]
        new_columns = other_columns + right_order
        df = df[new_columns]
        return df
    except Exception as e:
        # empty
        print("Error in downloading data.")
        print(e)
        cursor.execute(
            """
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            DROP VIEW IF EXISTS %s CASCADE;
            """, [reward_values_view, context_values_view, arm_assignments_view, arm_reward_merged_view, arm_reward_merged_max_view, contexts_merged_view, contexts_merged_max_view]
        )
        cursor.close()
        df = pd.DataFrame()
        return df

def find_reward_variable(mooclet_name):
    cursor = conn.cursor()
    print(mooclet_name)
    cursor.execute("select id from engine_mooclet where name = %s;", [mooclet_name]);
    mooclet_id = cursor.fetchone()[0]

    cursor.execute("""
    SELECT variable_id, count(*) from engine_value where mooclet_id = %s AND policy_id IS NOT null AND version_id IS NOT null AND variable_id != 3 group by variable_id order by count(*) desc;
    """, [mooclet_id])

    variable_id = cursor.fetchone()[0]
    print(variable_id)
    cursor.execute("""
    SELECT name from engine_variable where id = %s;
    """, [variable_id])
    reward_variable_name = cursor.fetchone()[0]
    
    cursor.close()
    return reward_variable_name


@mooclet_datadownloader_api.route("/apis/analysis/data_downloader", methods=["POST"])
def data_downloader():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    try:
        mooclet_name = request.get_json()['mooclet_name']
        dataset_description = request.get_json()['dataset_description']
        reward_variable = find_reward_variable(mooclet_name)
        df = data_downloader_local_new(mooclet_name, reward_variable)

        # Adding datasets to mongodb.
        # data_dict = df.to_dict('records')

        # Create document dictionary
        print("*****************************")
        binary_data = pickle.dumps(df)
        document = {
            'datasetDescription': dataset_description,
            'dataset': binary_data, 
            'mooclet': mooclet_name
        }
        Dataset.insert_one(document)
        print("downloading...")
        csv_string = df.to_csv(index=False)

        # Create a Flask response object with the CSV data
        response = make_response(csv_string)

        # Set the headers to tell the browser to download the file as a CSV
        response.headers['Content-Disposition'] = 'attachment; filename=data.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
    except Exception as e:
        print(e)
        return json_util.dumps({
            "status_code": 400, 
            "message": e
        }), 500