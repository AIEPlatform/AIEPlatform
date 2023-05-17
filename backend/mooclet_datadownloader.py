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

@mooclet_datadownloader_api.route("/apis/analysis/data_downloader", methods=["POST"])
def data_downloader():
    if check_if_loggedin() is False:
        return json_util.dumps({
            "status_code": 403,
        }), 403
    # GET DATA
    try:
        data = request.get_json()
        mooclet_name = data['mooclet_name']
        reward_variable_name = data['reward_variable_name']
        dataset_description = data['dataset_description']
        the_dataset = Dataset.find_one({"datasetDescription": dataset_description})
        if the_dataset is not None:
            return json_util.dumps({
                "status_code": 400, 
                "message": "Dataset Description already links to one dataset."
            }), 400
        
        
        cursor = conn.cursor()
        cursor.execute("select id from engine_mooclet where name = %s;", [mooclet_name]);
        mooclet_id = cursor.fetchone()[0]
        cursor.execute("""
            -- Prepare Tables before merging

            -- TESTING variables
            -- mooclet id: 2
            -- reward id: 10

            -- Mooclets
            DROP TABLE IF EXISTS data_download_mooclet CASCADE;

            CREATE TABLE data_download_mooclet AS 
            TABLE "engine_mooclet" 
            WITH NO DATA;

            -- Variables
            DROP TABLE IF EXISTS data_download_variable CASCADE;

            CREATE TABLE data_download_variable AS 
            TABLE "engine_variable" 
            WITH NO DATA;

            -- Versions
            DROP TABLE IF EXISTS data_download_version CASCADE;

            CREATE TABLE data_download_version AS 
            TABLE "engine_version" 
            WITH NO DATA;

            -- Learners
            DROP TABLE IF EXISTS data_download_learner CASCADE;

            CREATE TABLE data_download_learner AS 
            TABLE "engine_learner" 
            WITH NO DATA;

            -- Policies
            DROP TABLE IF EXISTS data_download_policy CASCADE;

            CREATE TABLE data_download_policy AS 
            TABLE "engine_policy" 
            WITH NO DATA;

            -- Policy Parameters
            DROP TABLE IF EXISTS data_download_policyparameters CASCADE;

            CREATE TABLE data_download_policyparameters AS 
            TABLE "engine_policyparameters" 
            WITH NO DATA;

            -- Policy Parameters History
            DROP TABLE IF EXISTS data_download_policyparametershistory CASCADE;

            CREATE TABLE data_download_policyparametershistory AS 
            TABLE "engine_policyparametershistory" 
            WITH NO DATA;

            -- Values
            DROP TABLE IF EXISTS data_download_value CASCADE;

            CREATE TABLE data_download_value AS 
            TABLE "engine_value" 
            WITH NO DATA;

            -- Copy data from server
            DROP TABLE IF EXISTS variable_names CASCADE;
            DROP TABLE IF EXISTS context_names CASCADE;

            DROP VIEW IF EXISTS temp_mooclet CASCADE;
            DROP VIEW IF EXISTS temp_version CASCADE;
            DROP VIEW IF EXISTS temp_policy_parameters CASCADE;
            DROP VIEW IF EXISTS temp_policy_parameters_history CASCADE;
            DROP VIEW IF EXISTS temp_variable CASCADE;
            DROP VIEW IF EXISTS temp_policy CASCADE;
            DROP VIEW IF EXISTS temp_value CASCADE;
            DROP VIEW IF EXISTS temp_learner CASCADE;
            -- Get target mooclet given mooclet id or mooclet name
            CREATE VIEW temp_mooclet AS
            (WITH matching_id_mooclet AS (SELECT * FROM "engine_mooclet" WHERE id = %s) -- this is from the argument
            SELECT * FROM matching_id_mooclet 
            WHERE (SELECT COUNT(*) FROM matching_id_mooclet) = 1
            UNION
            SELECT * FROM "engine_mooclet"
            WHERE (SELECT COUNT(*) FROM matching_id_mooclet) = 0
            AND name = 'this is a dummy name'); -- this is from the argument

            -- Get all versions with the target mooclet
            CREATE VIEW temp_version AS
            (SELECT "engine_version".*
            FROM temp_mooclet, "engine_version"
            WHERE temp_mooclet.id = "engine_version".mooclet_id
            ORDER BY id ASC);

            -- Get current policy parameters with the target mooclet
            CREATE VIEW temp_policy_parameters AS
            (SELECT "engine_policyparameters".*
            FROM temp_mooclet, "engine_policyparameters"
            WHERE temp_mooclet.id = "engine_policyparameters".mooclet_id
            ORDER BY id ASC);

            -- Get history policy parameters with the target mooclet
            CREATE VIEW temp_policy_parameters_history AS
            (SELECT "engine_policyparametershistory".*
            FROM temp_mooclet, "engine_policyparametershistory"
            WHERE temp_mooclet.id = "engine_policyparametershistory".mooclet_id
            ORDER BY id ASC);

            -- Get all variables that is used in policy parameters, or given reward name or id
            CREATE TABLE context_names (
                name text
            );

            INSERT into context_names 
            select distinct(name) from (select * from engine_value where mooclet_id = 7) t1 JOIN engine_variable on (t1.variable_id = engine_variable.id  and engine_variable.name != 'version' and engine_variable.name != %s);


            CREATE TABLE variable_names AS
            (SELECT DISTINCT(parameters->>'outcome_variable') AS name FROM temp_policy_parameters
            UNION
            SELECT DISTINCT(parameters->>'outcome_variable_name') AS name FROM temp_policy_parameters
            UNION
            SELECT DISTINCT(parameters->>'outcome_variable') AS name FROM temp_policy_parameters_history
            UNION
            SELECT DISTINCT(parameters->>'outcome_variable_name') AS name FROM temp_policy_parameters_history);

            DELETE FROM context_names WHERE name IS NULL OR name = 'version';

            CREATE VIEW temp_variable AS
            (SELECT DISTINCT * 
            FROM "engine_variable" 
            WHERE "engine_variable".name = 'version'
                OR "engine_variable".name = %s -- this is from the argument
                OR "engine_variable".name IN (SELECT name FROM context_names)
            ORDER BY id ASC);

            INSERT INTO variable_names
            (SELECT temp_variable.name FROM temp_variable);

            DELETE FROM variable_names WHERE name IS NULL;

            -- Get all policies involved in the target mooclet
            CREATE VIEW temp_policy AS
            (WITH policies AS
            (SELECT policy_id as id FROM temp_policy_parameters
            UNION
            SELECT policy_id as id FROM temp_policy_parameters_history)
            SELECT DISTINCT("engine_policy".*)
            FROM policies, "engine_policy"
            WHERE policies.id = "engine_policy".id
            ORDER BY id ASC);

            -- Get all values with the target mooclet
            CREATE VIEW temp_value AS
            (SELECT "engine_value".*
            FROM temp_mooclet, "engine_value"
            WHERE temp_mooclet.id = "engine_value".mooclet_id
            ORDER BY id ASC);

            -- Get all learners involved in the target mooclet
            CREATE VIEW temp_learner AS
            (SELECT DISTINCT("engine_learner".*)
            FROM temp_value, "engine_learner"
            WHERE temp_value.learner_id IS NOT NULL
                AND temp_value.learner_id = "engine_learner".id
            ORDER BY id ASC);

            -- Insert to tables
            INSERT INTO data_download_mooclet
            (SELECT * FROM temp_mooclet);

            INSERT INTO data_download_version
            (SELECT * FROM temp_version);

            INSERT INTO data_download_policyparameters
            (SELECT * FROM temp_policy_parameters);

            INSERT INTO data_download_policyparametershistory
            (SELECT * FROM temp_policy_parameters_history);

            INSERT INTO data_download_variable
            (SELECT * FROM temp_variable);

            INSERT INTO data_download_policy
            (SELECT * FROM "engine_policy");

            INSERT INTO data_download_value
            (SELECT * FROM temp_value);

            INSERT INTO data_download_learner
            (SELECT * FROM temp_learner);

            -- SELECT column_name, data_type
            -- FROM information_schema.columns
            -- WHERE table_schema = 'public' AND 
            -- table_name = 'data_download_variable';

            DROP VIEW IF EXISTS arm_value CASCADE;
            DROP VIEW IF EXISTS context_value CASCADE;
            DROP VIEW IF EXISTS reward_value CASCADE;
            DROP VIEW IF EXISTS arm_reward_merged CASCADE;
            DROP VIEW IF EXISTS context_merged CASCADE;

            DROP TABLE IF EXISTS data_download_dataprocess CASCADE;

            -- Get arm value
            CREATE VIEW arm_value AS
            (WITH version_variable AS (SELECT id FROM data_download_variable WHERE name = 'version')
            SELECT 
                data_download_value.*,
                data_download_version.name AS arm_name
            FROM data_download_version, data_download_value, version_variable
            WHERE data_download_value.version_id IS NOT NULL
                AND data_download_value.variable_id IS NOT NULL
                AND data_download_version.id = data_download_value.version_id
                AND version_variable.id = data_download_value.variable_id
            ORDER BY data_download_value.timestamp ASC);

            -- Get context value
            CREATE VIEW context_value AS
            (WITH context_variable AS 
                (SELECT 
                    data_download_variable.id AS id,
                    data_download_variable.name AS name
                FROM data_download_variable, context_names 
                WHERE data_download_variable.name = context_names.name)
            SELECT 
                data_download_value.*,
                context_variable.name AS context_name
            FROM data_download_value, context_variable
            WHERE data_download_value.variable_id IS NOT NULL
                AND context_variable.id = data_download_value.variable_id
            ORDER BY data_download_value.timestamp ASC);

            -- Get reward value
            CREATE VIEW reward_value AS
            (WITH reward_variable AS
                (WITH reward_variable_names AS
                    (SELECT name FROM variable_names WHERE name != 'version'
                    EXCEPT
                    SELECT name FROM context_names)
                SELECT 
                    data_download_variable.id AS id,
                    data_download_variable.name AS name
                FROM data_download_variable, reward_variable_names
                WHERE data_download_variable.name = reward_variable_names.name)
            SELECT 
                data_download_value.*,
                reward_variable.name AS reward_name
            FROM data_download_value, reward_variable
            WHERE data_download_value.variable_id IS NOT NULL
                AND reward_variable.id = data_download_value.variable_id
            ORDER BY data_download_value.timestamp ASC);

            -- (1) Merge arm value and reward value
            CREATE VIEW arm_reward_merged AS
            (SELECT DISTINCT * 
            FROM
                (SELECT 
                    max(reward_var_id) OVER w2 AS reward_var_id,
                    max(reward_name) OVER w2 AS reward_name,
                    max(value) OVER w2 AS value,
                    max(reward_text) OVER w2 AS reward_text,
                    max(reward_create_time) OVER w2 AS reward_create_time,
                    max(arm_var_id) OVER w2 AS arm_var_id,
                    max(arm_name) OVER w2 AS arm_name,
                    max(arm_text) OVER w2 AS arm_text,
                    max(arm_assign_time) OVER w2 AS arm_assign_time,
                    mooclet_id,
                    learner_id,
                    policy_id,
                    version_id
                FROM
                    (SELECT 
                        *, 
                        count(arm_var_id) OVER w1 AS grp
                    FROM
                        (SELECT 
                            value, 
                            NULL::character varying (100) AS arm_name,
                            reward_name,
                            NULL::text AS arm_text,
                            text AS reward_text,
                            NULL::timestamp with time zone AS arm_assign_time,
                            timestamp AS reward_create_time,
                            learner_id,
                            mooclet_id,
                            policy_id,
                            version_id,
                            variable_id AS reward_var_id, 
                            NULL::integer AS arm_var_id,
                            timestamp
                        FROM reward_value
                        UNION ALL
                        SELECT 
                            NULL::double precision AS value, 
                            arm_name,
                            NULL::character varying (100) AS reward_name,
                            text AS arm_text,
                            NULL::text AS reward_text,
                            timestamp AS arm_assign_time,
                            NULL::timestamp with time zone AS reward_create_time,
                            learner_id,
                            mooclet_id,
                            policy_id,
                            version_id,
                            NULL::integer AS reward_var_id, 
                            variable_id AS arm_var_id,
                            timestamp
                        FROM arm_value
                        ) s1
                    WINDOW w1 AS (PARTITION BY mooclet_id, version_id, policy_id, learner_id ORDER BY timestamp)
                    ) s2
                WINDOW w2 AS (PARTITION BY mooclet_id, version_id, policy_id, learner_id, grp)) s3
            WHERE arm_assign_time is NOT NULL
            ORDER BY arm_assign_time);

            -- (2) Merge context value
            -- (2) Merge context value
            CREATE VIEW context_merged AS
            (WITH context_before_arm AS
                (SELECT 
                    MAX(context_value.timestamp) AS timestamp, 
                    MAX(context_value.context_name) AS context_name, 
                    context_value.variable_id, 
                    arm_reward_merged.arm_assign_time
                FROM context_value, arm_reward_merged
                WHERE context_value.learner_id = arm_reward_merged.learner_id
                    AND context_value.mooclet_id = arm_reward_merged.mooclet_id
                    AND context_value.timestamp < arm_reward_merged.arm_assign_time
                GROUP BY context_value.variable_id, arm_reward_merged.arm_assign_time)
            SELECT *
            FROM
                (SELECT 
                    max(mooclet_id) AS mooclet_id,
                    max(learner_id) AS learner_id,
                    max(reward_var_id) AS reward_var_id,
                    max(reward_name) AS reward_name,
                    max(value) AS value,
                    max(reward_text) AS reward_text,
                    max(reward_create_time) AS reward_create_time,
                    max(arm_var_id) AS arm_var_id,
                    max(version_id) AS version_id,
                    max(arm_name) AS arm_name,
                    max(arm_text) AS arm_text,
                    arm_assign_time,
                    json_agg(
                        json_build_object(
                            'variable_id', variable_id, 
                            'name', context_name,
                            'value', context_value, 
                            'text', text, 
                            'timestamp', timestamp
                        )
                    ) AS contexts,
                    max(policy_id) AS policy_id
                FROM 
                    (SELECT 
                        s3.value AS context_value,
                        s3.text,
                        s3.variable_id,
                        s3.timestamp,
                        s3.context_name,
                        arm_reward_merged.reward_var_id,
                        arm_reward_merged.reward_name,
                        arm_reward_merged.value,
                        arm_reward_merged.reward_text,
                        arm_reward_merged.reward_create_time,
                        arm_reward_merged.arm_var_id,
                        arm_reward_merged.arm_name,
                        arm_reward_merged.arm_text,
                        arm_reward_merged.arm_assign_time,
                        arm_reward_merged.mooclet_id,
                        arm_reward_merged.learner_id,
                        arm_reward_merged.policy_id,
                        arm_reward_merged.version_id
                    FROM 
                        arm_reward_merged
                    FULL OUTER JOIN
                        (SELECT 
                            context_value.*,
                            context_before_arm.arm_assign_time
                        FROM context_value, context_before_arm
                        WHERE context_value.timestamp = context_before_arm.timestamp
                        AND context_value.variable_id = context_before_arm.variable_id
                        ) s3
                    ON arm_reward_merged.arm_assign_time = s3.arm_assign_time 
                    ) s1
                GROUP BY arm_assign_time) s2);

            -- (4) Merge policy parameters
            -- (5) Insert to final table
            CREATE TABLE data_download_dataprocess AS 
            (WITH policy_param_history_after_arm AS
                (SELECT 
                    MIN(data_download_policyparametershistory.creation_time) AS creation_time,  
                    context_merged.arm_assign_time
                FROM context_merged, data_download_policyparametershistory
                WHERE data_download_policyparametershistory.policy_id = context_merged.policy_id
                    AND data_download_policyparametershistory.mooclet_id = context_merged.mooclet_id
                    AND data_download_policyparametershistory.creation_time > context_merged.arm_assign_time
                GROUP BY context_merged.arm_assign_time)
            SELECT 
                s5.mooclet_id,
                s5.mooclet_name,
                s4.learner_id,
                s4.learner_name,
                s3.reward_var_id,
                s3.reward_name,
                s3.value,
                s3.reward_text,
                s3.reward_create_time,
                s3.arm_var_id,
                s3.version_id,
                s3.arm_name,
                s3.arm_text,
                s3.arm_assign_time,
                s3.contexts,
                s6.policy_id,
                s6.policy_name,
                s3.parameters,
                s3.creation_time
            FROM
                (SELECT
                    context_merged.*,
                    data_download_policyparametershistory.parameters,
                    data_download_policyparametershistory.creation_time
                FROM data_download_policyparametershistory, context_merged, policy_param_history_after_arm
                WHERE data_download_policyparametershistory.policy_id = context_merged.policy_id
                    AND data_download_policyparametershistory.mooclet_id = context_merged.mooclet_id
                    AND data_download_policyparametershistory.creation_time = policy_param_history_after_arm.creation_time
                    AND context_merged.arm_assign_time = policy_param_history_after_arm.arm_assign_time
                UNION ALL
                SELECT 
                    s2.*,
                    data_download_policyparameters.parameters,
                    data_download_policyparameters.latest_update AS creation_time
                FROM
                    (SELECT 
                        context_merged.*
                    FROM  
                        context_merged LEFT JOIN
                        (SELECT  
                            context_merged.arm_assign_time
                        FROM context_merged, data_download_policyparametershistory
                        WHERE data_download_policyparametershistory.policy_id = context_merged.policy_id
                            AND data_download_policyparametershistory.mooclet_id = context_merged.mooclet_id
                            AND data_download_policyparametershistory.creation_time > context_merged.arm_assign_time
                        GROUP BY context_merged.arm_assign_time) s1
                    ON context_merged.arm_assign_time = s1.arm_assign_time
                    WHERE s1.arm_assign_time IS NULL) s2 LEFT JOIN
                        data_download_policyparameters
                    ON data_download_policyparameters.policy_id = s2.policy_id
                ORDER BY arm_assign_time) s3
            LEFT JOIN (SELECT id as learner_id, name as learner_name FROM data_download_learner) s4
            ON s3.learner_id = s4.learner_id
            LEFT JOIN (SELECT id as mooclet_id, name as mooclet_name FROM data_download_mooclet) s5
            ON s3.mooclet_id = s5.mooclet_id
            LEFT JOIN (SELECT id as policy_id, name as policy_name FROM data_download_policy) s6
            ON s3.policy_id = s6.policy_id);

            select * from data_download_dataprocess;
        """, [mooclet_id, reward_variable_name, reward_variable_name])

        result = cursor.fetchall()

        if(len(result) == 0):
            return json_util.dumps({
                "status_code": 404, 
                "message": "Dataset is empty."
            }), 404
        
        
        cursor.close()
        df = pd.DataFrame(data = result, columns= [i[0] for i in cursor.description])

        result = []
        available_contextual_names = []
        for i, row in df.iterrows():
            for context in row['contexts']:
                if context['name'] not in available_contextual_names and context['name'] != None:
                    available_contextual_names.append(context['name'])

        for i, row in df.iterrows():

            row_formatted = {
                    "learner_id": row['learner_id'], 
                    "reward": row['value'], 
                    "reward_time": row['reward_create_time'], 
                    "arm": row['arm_name'], 
                    "arm_time": row['arm_assign_time'], 
                    'policy': row['policy_name'], 
                    'parameters': row['parameters']
            }

            for available_contextual_name in available_contextual_names:
                is_added = False
                for context in row['contexts']:
                    if context['name'] == available_contextual_name:
                        row_formatted[f'CONTEXTUAL_{available_contextual_name}'] = context['value'] 
                        row_formatted[f'CONTEXTUAL_{available_contextual_name}_time'] = context['timestamp']
                        is_added = True
                        break
                if not is_added:
                    row_formatted[f'CONTEXTUAL_{available_contextual_name}'] = np.nan
                    row_formatted[f'CONTEXTUAL_{available_contextual_name}_time'] = np.nan

            result.append(row_formatted)

        df = pd.DataFrame(result)
        df = df[df['learner_id'].notna()]
        df['learner_id'] = df['learner_id'].astype('int')


        df['arm_time'] = pd.to_datetime(df['arm_time'])
        df['arm_time'] = df['arm_time'].astype(object).where(df['arm_time'].notnull(), None)
        df['reward_time'] = pd.to_datetime(df['reward_time'])
        df['reward_time'] = df['reward_time'].astype(object).where(df['reward_time'].notnull(), None)
        for available_contextual_name in available_contextual_names:
            df[f'CONTEXTUAL_{available_contextual_name}_time'] = pd.to_datetime(df[f'CONTEXTUAL_{available_contextual_name}_time'])
            df[f'CONTEXTUAL_{available_contextual_name}_time'] = df[f'CONTEXTUAL_{available_contextual_name}_time'].astype(object).where(df[f'CONTEXTUAL_{available_contextual_name}_time'].notnull(), None)            




        # Adding datasets to mongodb.
        data_dict = df.to_dict('records')

        # Create document dictionary
        document = {
            'datasetDescription': dataset_description,
            'dataset': data_dict
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
        cursor.close()
        return json_util.dumps({
            "status_code": 400, 
            "message": e
        }), 500