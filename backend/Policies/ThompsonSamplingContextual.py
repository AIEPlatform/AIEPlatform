import random
import datetime
from credentials import *
from Policies.policy import Policy
from numpy.random import choice, beta
import numpy as np
from scipy.stats import invgamma
from helpers import *
from multiprocessing import Process
import os
import time
import threading


USER_CAN_WAIT_FOR_MODEL_UPDATE = 5
lock = threading.Lock()

class ThompsonSamplingContextual(Policy):

    # Draw thompson sample of (reg. coeff., variance) and also select the optimal action
    # thompson sampling policy with contextual information.
    # Outcome is estimated using bayesian linear regression implemented by NIG conjugate priors.
    # map dict to version
    # get the current user's context as a dict
    # store normal-inverse-gamma parameters
    # 
    # 
    def __init__(self, **mooclet_obj_from_db):
        super().__init__(**mooclet_obj_from_db)
        regression_formula = "reward~"
        items = []
        possible_variables = []
        for regression_formula_item in self.parameters['regressionFormulaItems']:
            temp = [d['name'] for d in regression_formula_item]
            possible_variables.extend(regression_formula_item)
            items.append('*'.join(temp))
        regression_formula += ('+'.join(items))
        self.parameters['regression_formula'] = regression_formula

        # TODO: Improve the frequency.
        # get contextual variable lists.
        possible_variables = possible_variables

        contextuals_variables = [possible_variable['name'] for possible_variable in possible_variables if possible_variable in self.study['variables']]
        self.parameters['contextual_variables'] = list(set(contextuals_variables))


        #TODO: read this from frontend.
        if_intercept = int(self.parameters['include_intercept'])
        coef_cov = np.identity(len(self.parameters['regressionFormulaItems']) + if_intercept)
        coef_mean = np.zeros(len(self.parameters['regressionFormulaItems']) + if_intercept)

        if 'coef_cov' in self.parameters:
            coef_cov = self.parameters['coef_cov']
        if 'coef_mean' in self.parameters:
            coef_mean = self.parameters['coef_mean']
        self.parameters['coef_cov'] = coef_cov
        self.parameters['coef_mean'] = coef_mean

    def choose_arm(self, user, where, other_information):
        current_time = datetime.datetime.now()
        lucky_version = self.get_consistent_assignment(user, where)
        if self.should_update_model(current_time):

            someone_is_updating = False
            lock.acquire()
            print(f'{user} checking lock...')
            # TODO: check if it prevents the lock being occupied infinitely.
            try:
                new_lock_id = check_lock(self._id)
            except Exception as e:
                print(e)
                print("error in check_lock")
                new_lock_id = None
            if new_lock_id is None:
                someone_is_updating = True
                print(f'{user} finds someone\'s updating the model...')
            lock.release()
            if not someone_is_updating:
                print(f'{user} updating model..')
                p = threading.Thread(target=self.update_model, args=(new_lock_id, ))
                p.start()
                start_time = time.time()
                while p.is_alive():
                    if (time.time() - start_time) > USER_CAN_WAIT_FOR_MODEL_UPDATE:
                        # Timeout reached, proceed without waiting
                        break
                    time.sleep(0.5)  # Adjust the sleep interval if needed
        try:
            # because it's TS Contextual, 
            if lucky_version is None:
                all_versions = self.study['versions']
                all_versions = {d['name']: d['content'] for d in all_versions}
                parameters = self.parameters
                # Store regression equation string
                regression_formula = parameters['regression_formula']
                # Include intercept can be true or false

                include_intercept = parameters['include_intercept']
                # Store contextual variables
                
                contextual_vars = parameters['contextual_variables']
                
                # Get the contextual variables for the learner (most recent ones), or auto init ones.

                column_name = 'variableName'
                array_list = contextual_vars  # Example array list

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
                            column_name: 1,  # Sort ascending by column A
                            '_id': -1       # Sort descending by _id (to get the last occurrence)
                        }
                    },
                    {
                        '$group': {
                            '_id': '$' + column_name,
                            'last_document': {'$first': '$$ROOT'}
                        }
                    },
                    {
                        '$replaceRoot': {'newRoot': '$last_document'}
                    }
                ]

                # Execute the aggregation pipeline
                result = list(VariableValue.aggregate(pipeline))

                # Iterate over the array list
                for value in array_list:
                    has_document = False

                    # Check if a document exists for the current value
                    for document in result:
                        if document[column_name] == value:
                            has_document = True
                            break

                    # Insert a document into the other collection if no document exists
                    if not has_document:
                        document_to_insert = {
                            "variableName": value, 
                            'value': 1,   # TODO: impute based on a better rule.
                            'user': user,
                            'where': 'auto init', 
                            'timestamp': current_time
                        }
                        VariableValue.insert_one(document_to_insert)
                    
                contextual_values = list(VariableValue.aggregate(pipeline))

                contextual_vars_dict = {}
                contextual_vars_id_dict = {}

                for contextual_value in contextual_values:
                    contextual_vars_dict[contextual_value['variableName']] = contextual_value['value']
                    contextual_vars_id_dict[contextual_value['variableName']] = contextual_value['_id']
                
                current_enrolled = len(list(Interaction.find({"moocletId": self._id}))) #TODO: is it number of learners or number of observations????

                if "uniform_threshold" in parameters and current_enrolled < float(parameters["uniform_threshold"]):
                    lucky_version = random.choice(self.study['versions'])
                    # # TODO: Make a new interaction. Remember to indicate this is from uniform.
                    new_interaction = {
                        "user": user,
                        "treatment": lucky_version,
                        "outcome": None,
                        "where": where,
                        "moocletId": self._id,
                        "timestamp": datetime.datetime.now(),
                        "otherInformation": other_information, 
                        "contextuals": contextual_vars_dict,
                        "contextualIds": contextual_vars_id_dict, 
                        'isUniform': True
                    }
                    Interaction.insert_one(new_interaction)
                    return lucky_version
                
                mean = parameters['coef_mean']
                cov = parameters['coef_cov']
                variance_a = float(parameters['variance_a'])
                variance_b = float(parameters['variance_b'])
                
                
                precesion_draw = invgamma.rvs(variance_a, 0, variance_b, size=1)
                coef_draw = np.random.multivariate_normal(mean, precesion_draw * cov)
                
                # Compute outcome for each action
                best_outcome = -np.inf
                best_action = None


                for version in all_versions:
                    independent_vars = {}
                    for contextual_var in contextual_vars_dict:
                        independent_vars[contextual_var] = contextual_vars_dict[contextual_var]
                    for version2 in all_versions:
                        if version2 == version:
                            independent_vars[version2] = 1
                        else:
                            independent_vars[version2] = 0
                    outcome = calculate_outcome(independent_vars, coef_draw, include_intercept, regression_formula)
                    if best_action is None or outcome > best_outcome:
                        best_outcome = outcome
                        best_action = version

                lucky_version = next(version for version in self.study['versions'] if version['name'] == best_action)

            # Interaction
            # – learner
            # – treatment
            # – outcome
            # – where: like which page, which dialogue…
            # – MOOClet
            # – timestamp
            # – otherInformation
            
            # Insert a record for the interaction.

            new_interaction = {
                "user": user,
                "treatment": lucky_version,
                "outcome": None,
                "where": where,
                "moocletId": self._id,
                "timestamp": datetime.datetime.now(),
                "otherInformation": other_information, 
                "contextuals": contextual_vars_dict,
                "contextualIds": contextual_vars_id_dict
            }

            Interaction.insert_one(new_interaction)
            print(f'{user} gets a treatment...')
            return lucky_version
        except Exception as e:
            print(e)
            return None
        
    def get_reward(self, user, value, where, other_information):
        current_time = datetime.datetime.now()
        latest_interaction = self.get_latest_interaction(user, where)
        if latest_interaction is None:
            return 400
        else:
            print(f'{user} sends reward...')
            Interaction.update_one({'_id': latest_interaction['_id']}, {'$set': {'outcome': value, 'rewardTimestamp': current_time}})

            # Note that TS Contextual won't update inmediately.
            # We should do a check if to see if should update the parameters or not.
            if True:
                pass
            return 200

    def should_update_model(self, current_time):
        # TODO: consider if we should have a time filter.
        # TODO: consider if we can make sure that everything after this interaction are not used??
        earliest_unused = Interaction.find_one(
                        {"moocletId": self._id, "outcome": {"$ne": None}, "used": {"$ne": True}}, session=session
                         ) # TODO: Shall we exclute those from uniform (I don't think so?)
        if earliest_unused is None:
            return False
        if (current_time - earliest_unused['rewardTimestamp']).total_seconds() / 60 > float(self.parameters['updatedPerMinute']):
            return True
        else:
            return False
        
    def update_model(self, new_lock_id):
        # First, see if this is already being updated by someone.
        current_time = datetime.datetime.now()
        with client.start_session() as session:
            session.start_transaction()

            try:

                current_params = self.parameters
                coef_mean, coef_cov, variance_a, variance_b, include_intercept = current_params['coef_mean'], current_params['coef_cov'], float(current_params['variance_a']), float(current_params['variance_b']), float(current_params['include_intercept'])

                interactions_for_posterior = list(Interaction.find(
                    {"moocletId": self._id, "outcome": {"$ne": None}, "used": {"$ne": True}}, session=session
                    )) # TODO: Need to somehow tag interactions as having been used for posterior already or by time.
                
                Interaction.update_many(
                    {"moocletId": self._id, "outcome": {"$ne": None}, "used": {"$ne": True}}, {"$set": {"used": True}}, session=session
                    )
                numpy_rewards = np.array([interaction['outcome'] for interaction in interactions_for_posterior])
                
                regression_formula = current_params['regression_formula']
                all_versions = self.study['versions']
                all_versions = {d['name']: d['content'] for d in all_versions}

                formula = regression_formula.strip()

                # Split RHS of equation into variable list (context, action, interactions)
                vars_list = list(map(str.strip, formula.split('~')[1].split('+')))
                if include_intercept:
                    vars_list.insert(0,1.)

                # construct design matrix.
                design_matrix = np.zeros((len(interactions_for_posterior), len(vars_list)))
                for i in range(len(interactions_for_posterior)):
                    interaction = interactions_for_posterior[i]
                    contextual_vars_dict = interaction['contextuals']
                    independent_vars = contextual_vars_dict
                    for version in all_versions:
                        if version == interaction['treatment']['name']:
                            independent_vars[version] = 1
                        else:
                            independent_vars[version] = 0
                    for j in range(len(vars_list)):
                        var = vars_list[j]
                        ## Determine value in variable list
                        # Initialize value (can change in loop)
                        value = 1.
                        # Intercept has value 1
                        if type(var) == float:
                            value = 1.

                        # Interaction term value
                        elif '*' in var:
                            interacting_vars = var.split('*')
                            interacting_vars = list(map(str.strip,interacting_vars))
                            # Product of variable values in interaction term
                            for interacting_var in interacting_vars:
                                value *= independent_vars[interacting_var]
                        # Action or context value
                        else:
                            value = independent_vars[var]

                        design_matrix[i][j] = value
                posterior_vals = posteriors(numpy_rewards, design_matrix, coef_mean, coef_cov, variance_a, variance_b)

                # Update parameters in DB.
                MOOClet.update_one({"_id": self._id}, {"$set": {
                    "parameters.coef_mean": posterior_vals['coef_mean'].tolist(),
                    "parameters.coef_cov": posterior_vals['coef_cov'].tolist(),
                    "parameters.variance_a": posterior_vals['variance_a'],
                    "parameters.variance_b": posterior_vals['variance_b'],
                }}, session=session)
    
                # Release lock.
                session.commit_transaction()
                print(f'model updated successfully! Time spent: {(datetime.datetime.now() - current_time).total_seconds()} seconds')
                Lock.delete_one({"_id": new_lock_id})
                return
            except Exception as e:
                print(e)
                print(f'model update failed, rollback...')
                Lock.delete_one({"_id": new_lock_id})
                session.abort_transaction()
                return

# Compute expected reward given context and action of user
# Inputs: (design matrix row as dict, coeff. vector, intercept, reg. eqn.)
def calculate_outcome(var_dict, coef_list, include_intercept, formula):

    # :param var_dict: dict of all vars (actions + contextual) to their values
    # :param coef_list: coefficients for each term in regression
    # :param include_intercept: whether intercept is included
    # :param formula: regression formula
    # :return: outcome given formula, coefficients and variables values
    formula = formula

    # Split RHS of equation into variable list (context, action, interactions)
    vars_list = list(map(str.strip, formula.split('~')[1].split('+')))


    # Add 1 for intercept in variable list if specified
    if include_intercept:
        vars_list.insert(0,1.)

    # Raise assertion error if variable list different length then coeff list
    #print(vars_list)
    #print(coef_list)

    assert(len(vars_list) == len(coef_list))

    # Initialize outcome
    outcome = 0.
    coef_list = coef_list.tolist()

    ## Use variables and coeff list to compute expected reward
    # Itterate over all (var, coeff) pairs from regresion model
    num_loops = 0
    for j in range(len(coef_list)): #var, coef in zip(vars_list,coef_list):
        var = vars_list[j]
        coef = coef_list[j]
        ## Determine value in variable list
        # Initialize value (can change in loop)
        value = 1.
        # Intercept has value 1
        if type(var) == float:
            value = 1.

        # Interaction term value
        elif '*' in var:
            interacting_vars = var.split('*')

            interacting_vars = list(map(str.strip,interacting_vars))
            # Product of variable values in interaction term
            for i in range(0, len(interacting_vars)):
                value *= var_dict[interacting_vars[i]]
        # Action or context value
        else:
            value = var_dict[var]

        # Compute expected reward (hypothesized regression model)
        outcome += coef * value
        num_loops += 1

    return outcome


def check_lock(mooceltId):
    # Check if lock exists
    try:
        lock_exists = Lock.find_one({"mooceltId": mooceltId})
        if lock_exists:
            return None
        else:
            # Create lock
            response = Lock.insert_one({"mooceltId": mooceltId})
            return response.inserted_id
    except Exception as e:
        print(e)
        return None

def posteriors(y, X, m_pre, V_pre, a1_pre, a2_pre):
    #y = list of uotcomes
    #X = design matrix
    #priors input by users, but if no input then default
    #m_pre vector 0 v_pre is an identity matrix - np.identity(size of params) a1 & a2 both 2. save the updates
    #get the reward as a spearate vector. figure ut batch size issues (time based)

    # Data size

    datasize = len(y)

    # X transpose
    Xtranspose = np.matrix.transpose(X)

    # Residuals
    # (y - Xb) and (y - Xb)'
    resid = np.subtract(y, np.dot(X,m_pre))
    resid_trans = np.matrix.transpose(resid)

    # N x N middle term for gamma update
    # (I + XVX')^{-1}
    mid_term = np.linalg.inv(np.add(np.identity(datasize), np.dot(np.dot(X, V_pre),Xtranspose)))

    ## Update coeffecients priors

    # Update mean vector
    # [(V^{-1} + X'X)^{-1}][V^{-1}mu + X'y]
    m_post = np.dot(np.linalg.inv(np.add(np.linalg.inv(V_pre), np.dot(Xtranspose,X))), np.add(np.dot(np.linalg.inv(V_pre), m_pre), np.dot(Xtranspose,y)))

    # Update covariance matrix
    # (V^{-1} + X'X)^{-1}
    V_post = np.linalg.inv(np.add(np.linalg.inv(V_pre), np.dot(Xtranspose,X)))

    ## Update precesion prior

    # Update gamma parameters
    # a + n/2 (shape parameter)
    a1_post = a1_pre + datasize/2

    # b + (1/2)(y - Xmu)'(I + XVX')^{-1}(y - Xmu) (scale parameter)
    a2_post = a2_pre + (np.dot(np.dot(resid_trans, mid_term), resid))/2

    ## Posterior draws

    # Precesions from inverse gamma (shape, loc, scale, draws)
    precesion_draw = invgamma.rvs(a1_post, 0, a2_post, size = 1)

    # Coeffecients from multivariate normal
    beta_draw = np.random.multivariate_normal(m_post, precesion_draw*V_post)

    # List with beta and s^2
    #beta_s2 = np.append(beta_draw, precesion_draw)

    # Return posterior drawn parameters
    # output: [(betas, s^2, a1, a2), V]
    return{"coef_mean": m_post,
        "coef_cov": V_post,
        "variance_a": a1_post,
        "variance_b": a2_post}