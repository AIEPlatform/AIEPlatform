import random
import datetime
from credentials import *
from Policies.policy import Policy
from numpy.random import choice, beta
import numpy as np
from scipy.stats import invgamma
from helpers import *
from impute import *
import traceback
from Models.VariableValueModel import VariableValueModel
from Models.InteractionModel import InteractionModel
from Models.AssignerModel import AssignerModel
from errors import *


USER_CAN_WAIT_FOR_MODEL_UPDATE = 0.5

class ThompsonSamplingContextual(Policy):
    # TODO
    # make a static method called validate assigner.
    @staticmethod
    def validate_assigner(assigner):
        # check if cov matrix and mean are numeric.
        try:
            assigner['parameters']['coef_cov'] = [[float(num) for num in row] for row in assigner['parameters']['coef_cov']]
        except ValueError as e:
            raise ValueError("Invalid numeric string found in the coefficient matrix") from e
        
        try:
            assigner['parameters']['coef_mean'] = [float(num) for num in assigner['parameters']['coef_mean']]
        except ValueError as e:
            raise ValueError("Invalid numeric string found in the coefficient mean") from e
        
        return assigner
        
        
    # Draw thompson sample of (reg. coeff., variance) and also select the optimal action
    # thompson sampling policy with contextual information.
    # Outcome is estimated using bayesian linear regression implemented by NIG conjugate priors.
    # map dict to version
    # get the current user's context as a dict
    # store normal-inverse-gamma parameters
    # 
    # 
    def __init__(self, user, **assigner_obj_from_db):
        super().__init__(user, **assigner_obj_from_db)
        self.individualMode = False
        # TODO: check if num_rewards is strictly the same as the threshold when it's init.
        if 'individualLevel' in self.parameters and self.parameters['individualLevel'] is True and InteractionModel.get_assigner_num_feedback(assignerId = self._id) >= self.parameters['individualLevelThreshold']:
            # load or init.
            self.individualMode = True
            theIndividualInformation = AssignerIndividualLevelInformation.find_one({"assignerId": self._id, "user": user})
            if theIndividualInformation is not None:
                self.parameters = theIndividualInformation['parameters']
            else:
                # TODO: Do we need lock here? Is it possible that the concurrency issue happens for one user?
                current_params = {key: value for key, value in self.parameters.items() if key not in  ["individualParameters", "individualLevel", "individualLevelThreshold", "individualLevelBatchSize", "batch_size"]}
                current_params['batch_size'] = self.parameters["individualLevelBatchSize"]
                response = AssignerIndividualLevelInformation.insert_one({"assignerId": self._id, "user": user, "parameters": current_params})
                the_info = AssignerIndividualLevelInformation.find_one({"_id": response.inserted_id})
                self.parameters = the_info['parameters']

        self.parameters['regressionFormulaItems'] = expand_categorical_variables(self.parameters['regressionFormulaItems'])

        regression_formula = "reward~"
        items = []
        possible_variables = []
        for regression_formula_item in self.parameters['regressionFormulaItems']:
            temp = regression_formula_item
            possible_variables.extend(regression_formula_item)
            items.append('*'.join(temp))
        regression_formula += ('+'.join(items))
        self.parameters['regression_formula'] = regression_formula



    def reinit(self):
        regression_formula = "reward~"
        items = []
        possible_variables = []
        self.parameters['regressionFormulaItems'] = expand_categorical_variables(self.parameters['regressionFormulaItems'])
        for regression_formula_item in self.parameters['regressionFormulaItems']:
            temp = regression_formula_item
            possible_variables.extend(regression_formula_item)
            items.append('*'.join(temp))
        regression_formula += ('+'.join(items))
        self.parameters['regression_formula'] = regression_formula


    def choose_arm_algorithm(self, user, where, other_information, request_different_arm = False):
        try:
            current_time = datetime.datetime.now()
            lucky_version = self.get_incomplete_consistent_assignment(user, where)
            

            # check if we should switch to individual
            if self.individualMode:
                return self.algorithm_individual(user, where, other_information)
                        
            # because it's TS Contextual, 
            if lucky_version is None:
                current_enrolled = InteractionModel.get_num_participants_for_assigner(assignerId = self._id)
                all_versions = self.get_all_versions(user, where, request_different_arm)
                if len(all_versions) == 0:
                    raise NoDifferentTreatmentAvailable("There is no unassigned version left.")
                parameters = self.parameters
                # Store regression equation string
                regression_formula = parameters['regression_formula']
                # Include intercept can be true or false

                include_intercept = parameters['include_intercept']
                # Store contextual variables
                
                contextual_vars = self.study['variables']
                # Get the contextual variables for the learner (most recent ones), or auto init ones.
                
                result = VariableValueModel.get_latest_variable_values(contextual_vars, user)
                
                # Iterate over the array list
                for value in contextual_vars:
                    has_document = False

                    # Check if a document exists for the current value
                    for document in result:
                        if document['variable'] == value:
                            has_document = True
                            break

                    
                    imputed_value = random_imputation(value) # TODO: in the future we need to check the Assigner's configuration to see which imputer to use.

                    # Insert a document into the other collection if no document exists
                    # get deployment_name

                    the_deployment = Deployment.find_one({"_id": self.study['deploymentId']})
                    if not has_document:
                        document_to_insert = {
                            'deployment': the_deployment['name'],
                            "variable": value, 
                            'value': imputed_value,   # TODO: impute based on a better rule.
                            'user': user,
                            'where': 'auto init', 
                            'timestamp': current_time
                        }
                        VariableValueModel.insert_variable_value(document_to_insert)
                    
                contextual_values = VariableValueModel.get_latest_variable_values(contextual_vars, user)

                contextual_vars_dict = {}
                contextual_vars_id_dict = {}

                for contextual_value in contextual_values:
                    contextual_vars_dict[contextual_value['variable']] = {"value": contextual_value['value'], "timestamp": contextual_value['timestamp']}
                    contextual_vars_id_dict[contextual_value['variable']] = contextual_value['_id']

                if "uniform_threshold" in parameters and current_enrolled < float(parameters["uniform_threshold"]):
                    
                    lucky_version = random.choice(all_versions)
                    # # TODO: Make a new interaction. Remember to indicate this is from uniform.
                    new_interaction = {
                        "user": user,
                        "treatment": lucky_version,
                        "outcome": None,
                        "where": where,
                        "assignerId": self._id,
                        "timestamp": datetime.datetime.now(),
                        "otherInformation": other_information, 
                        "contextuals": contextual_vars_dict,
                        "contextualIds": contextual_vars_id_dict, 
                        'isUniform': True
                    }
                    InteractionModel.insert_one(new_interaction)
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
                        # TODO: check if the variable is a categorical variable or not.
                        the_variable = Variable.find_one({'name': contextual_var})
                        if the_variable['type'] == 'categorical':
                            # iterate over the min and max. make independent_vars[contextual_var + "::" + index] = 1 if it's the same as the value, otherwise 0.
                            for index in range(the_variable['min'], the_variable['max'] + 1):
                                if contextual_vars_dict[contextual_var]['value'] == index:
                                    independent_vars[contextual_var + "::" + str(index)] = 1
                                else:
                                    independent_vars[contextual_var + "::" + str(index)] = 0
                        else:
                            independent_vars[contextual_var] = contextual_vars_dict[contextual_var]['value']

                    independent_vars = {**independent_vars, **version['versionJSON']} #TODO: CHECK
                    outcome = calculate_outcome(independent_vars, coef_draw, include_intercept, regression_formula)
                    if best_action is None or outcome > best_outcome:
                        best_outcome = outcome
                        best_action = version

                lucky_version = best_action

            # Interaction
            # – learner
            # – treatment
            # – outcome
            # – where: like which page, which dialogue…
            # – Assigner
            # – timestamp
            # – otherInformation
            
            # Insert a record for the interaction.

                new_interaction = {
                    "user": user,
                    "treatment": lucky_version,
                    "outcome": None,
                    "where": where,
                    "assignerId": self._id,
                    "timestamp": datetime.datetime.now(),
                    "otherInformation": other_information, 
                    "contextuals": contextual_vars_dict,
                    "contextualIds": contextual_vars_id_dict
                }

                InteractionModel.insert_one(new_interaction)
            return lucky_version
        except:
            print(traceback.format_exc())



    # should_update_model_individual

    def should_update_model_individual(self, current_time, user):
        # TODO: consider if we should have a time filter.
        # TODO: consider if we can make sure that everything after this interaction are not used??
        earliest_unused = InteractionModel.find_earliest_unused(self._id, user)
        if earliest_unused is None:
            return False
        if (current_time - earliest_unused['rewardTimestamp']).total_seconds() / 60 > float(self.parameters['updatedPerMinute']):
            return True
        else:
            return False

    # update_model_individual

    def update_model_algorithm_individual(self, session):
        # First, see if this is already being updated by someone.
        user = self['user']
        current_time = datetime.datetime.now()
        current_params = self.parameters
        current_enrolled = InteractionModel.get_num_participants_for_assigner(assignerId = self._id) #TODO: is it number of learners or number of observations????
        
        if not (self.should_update_model(current_time) and current_enrolled % self.parameters['batch_size'] == 0): return
        # TODO: Check by this step, the user must have its individualParameter created.
        try:
            coef_mean, coef_cov, variance_a, variance_b, include_intercept = current_params['coef_mean'], current_params['coef_cov'], float(current_params['variance_a']), float(current_params['variance_b']), float(current_params['include_intercept'])

            # use_unused_interactions

            interactions_for_posterior = InteractionModel.use_unused_interactions(self._id, user, session=session)
            
            numpy_rewards = np.array([interaction['outcome'] for interaction in interactions_for_posterior])

            regression_formula = current_params['regression_formula']
            all_versions = self.study['versions']

            formula = regression_formula.strip()

            # Split RHS of equation into variable list (context, action, interactions)
            vars_list = list(map(str.strip, formula.split('~')[1].split('+')))
            if include_intercept:
                vars_list.insert(0,1.)

            # construct design matrix.
            design_matrix = np.zeros((len(interactions_for_posterior), len(vars_list)))
            for i in range(len(interactions_for_posterior)):
                interaction = interactions_for_posterior[i]
                contextual_vars_dict = {}


                for key, sub_dict in interaction['contextuals'].items():
                    contextual_vars_dict[key] = sub_dict["value"]
                    
                independent_vars = {}
                for contextual_var in contextual_vars_dict:
                    # TODO: check if the variable is a categorical variable or not.
                    the_variable = Variable.find_one({'name': contextual_var})
                    if the_variable['type'] == 'categorical':
                        # iterate over the min and max. make independent_vars[contextual_var + "::" + index] = 1 if it's the same as the value, otherwise 0.
                        for index in range(the_variable['min'], the_variable['max'] + 1):
                            if contextual_vars_dict[contextual_var]['value'] == index:
                                independent_vars[contextual_var + "::" + str(index)] = 1
                            else:
                                independent_vars[contextual_var + "::" + str(index)] = 0
                    else:
                        independent_vars[contextual_var] = contextual_vars_dict[contextual_var]['value']

                independent_vars = {**independent_vars, **version['versionJSON']} #TODO: CHECK
                # for version in all_versions:
                #     if version == interaction['treatment']['name']:
                #         independent_vars[version] = 1
                #     else:
                #         independent_vars[version] = 0


                versionName = interaction['treatment']['name']
                # TODO: I don't want to use the versionJSON saved in the interaction, because the versionJSON might have changed. (and we shouldn't saved the version json in the interaction, we need to remove it for the future!)
                version = next(version for version in all_versions if version['name'] == versionName)

                independent_vars = {**independent_vars, **version['versionJSON']} #TODO: CHECK

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
            AssignerIndividualLevelInformation.update_one({"assignerId": self._id, "user": user}, {"$set": {"parameters": {
                "coef_mean": posterior_vals['coef_mean'].tolist(),
                "coef_cov": posterior_vals['coef_cov'].tolist(),
                "variance_a": posterior_vals['variance_a'],
                "variance_b": posterior_vals['variance_b'],
                "include_intercept": include_intercept,
                "batch_size": current_params['batch_size'],
                "uniform_threshold": current_params['uniform_threshold'],
                "updatedPerMinute": current_params['updatedPerMinute'],
                "regressionFormulaItems": current_params['regressionFormulaItems'],
            }}}, session=session)

            # Release lock.
            session.commit_transaction()
            print(f'individual model updated successfully! Time spent: {(datetime.datetime.now() - current_time).total_seconds()} seconds')
            self.paramters = AssignerIndividualLevelInformation.find_one({"assignerId": self._id, "user": user})['parameters']
            self.reinit()
            return
        except Exception as e:
            print(f'model update failed')
            return

    def should_update_model(self, current_time):
        # TODO: consider if we should have a time filter.
        # TODO: consider if we can make sure that everything after this interaction are not used??
        earliest_unused = InteractionModel.find_earliest_unused(self._id)
        if earliest_unused is None:
            return False
        if (current_time - earliest_unused['rewardTimestamp']).total_seconds() / 60 > float(self.parameters['updatedPerMinute']):
            return True
        else:
            return False
        
    def update_model_algorithm(self, session):
        current_time = datetime.datetime.now()
        # First, see if this is already being updated by someone.
        # check if we should switch to individual
        if self.individualMode:
            return self.update_model_algorithm_individual(session)
        current_enrolled = InteractionModel.get_num_participants_for_assigner(assignerId = self._id) #TODO: is it number of learners or number of observations????
        if not(self.should_update_model(current_time) and current_enrolled % self.parameters['batch_size'] == 0): return
        try:
            current_params = self.parameters
            coef_mean, coef_cov, variance_a, variance_b, include_intercept = current_params['coef_mean'], current_params['coef_cov'], float(current_params['variance_a']), float(current_params['variance_b']), float(current_params['include_intercept'])

            # use_unused_interactions

            interactions_for_posterior = InteractionModel.use_unused_interactions(self._id, None, session=session)
            
            numpy_rewards = np.array([interaction['outcome'] for interaction in interactions_for_posterior])
            
            regression_formula = current_params['regression_formula']
            all_versions = self.study['versions']

            formula = regression_formula.strip()

            # Split RHS of equation into variable list (context, action, interactions)
            vars_list = list(map(str.strip, formula.split('~')[1].split('+')))
            if include_intercept:
                vars_list.insert(0,1.)

            # TODO: expand the vars_list if there are categorical variables.

            # construct design matrix.
            design_matrix = np.zeros((len(interactions_for_posterior), len(vars_list)))
            for i in range(len(interactions_for_posterior)):
                interaction = interactions_for_posterior[i]
                contextual_vars_dict = {}


                for key, sub_dict in interaction['contextuals'].items():
                    contextual_vars_dict[key] = sub_dict["value"]

                    
                independent_vars = {}
                for contextual_var in contextual_vars_dict:
                    # TODO: check if the variable is a categorical variable or not.
                    the_variable = Variable.find_one({'name': contextual_var})
                    if the_variable['type'] == 'categorical':
                        # iterate over the min and max. make independent_vars[contextual_var + "::" + index] = 1 if it's the same as the value, otherwise 0.
                        for index in range(the_variable['min'], the_variable['max'] + 1):
                            if contextual_vars_dict[contextual_var] == index:
                                independent_vars[contextual_var + "::" + str(index)] = 1
                            else:
                                independent_vars[contextual_var + "::" + str(index)] = 0
                    else:
                        independent_vars[contextual_var] = contextual_vars_dict[contextual_var]


                versionName = interaction['treatment']['name']
                # TODO: I don't want to use the versionJSON saved in the interaction, because the versionJSON might have changed. (and we shouldn't saved the version json in the interaction, we need to remove it for the future!)
                version = next(version for version in all_versions if version['name'] == versionName)

                independent_vars = {**independent_vars, **version['versionJSON']} #TODO: CHECK


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
            AssignerModel.update_policy_parameters(self._id, {
                "parameters.coef_mean": posterior_vals['coef_mean'].tolist(),
                "parameters.coef_cov": posterior_vals['coef_cov'].tolist(),
                "parameters.variance_a": posterior_vals['variance_a'],
                "parameters.variance_b": posterior_vals['variance_b'],
            }, session)

            # Release lock.
            print(f'group model updated successfully! Time spent: {(datetime.datetime.now() - current_time).total_seconds()} seconds')
            self.paramters = AssignerModel.find_assigner({"_id": self._id})['parameters']
            self.reinit()
            return
        except Exception as e:
            print(traceback.format_exc())
            print(f'model update failed')


    # get_num_participants_for_assigner_individual
    def choose_arm_algorithm_individual(self, user, where, other_information):
        current_time = datetime.datetime.now()
        try:
            # because it's TS Contextual, 
            if lucky_version is None:
                all_versions = self.study['versions']
                # TODO: what if this doesn't exist? Copy over! But should it happen here?
                parameters = self.parameters
                # Store regression equation string
                regression_formula = parameters['regression_formula']
                # Include intercept can be true or false

                include_intercept = parameters['include_intercept']
                # Store contextual variables
                
                contextual_vars = self.study['variables']
                # Get the contextual variables for the learner (most recent ones), or auto init ones.

                result = VariableValueModel.get_latest_variable_values(contextual_vars, user)
                
                # Iterate over the array list
                for value in contextual_vars:
                    has_document = False

                    # Check if a document exists for the current value
                    for document in result:
                        if document['variable'] == value:
                            has_document = True
                            break


                    imputed_value = random_imputation(value) # TODO: in the future we need to check the Assigner's configuration to see which imputer to use.

                    # Insert a document into the other collection if no document exists
                    the_deployment = Deployment.find_one({"_id": self.study['deploymentId']})
                    if not has_document:
                        document_to_insert = {
                            'deployment': the_deployment['name'],
                            "variable": value, 
                            'value': imputed_value,   # TODO: impute based on a better rule.
                            'user': user,
                            'where': 'auto init', 
                            'timestamp': current_time
                        }
                        VariableValueModel.insert_variable_value(document_to_insert)
                    
                contextual_values = VariableValueModel.get_latest_variable_values(contextual_vars, user)

                contextual_vars_dict = {}
                contextual_vars_id_dict = {}

                for contextual_value in contextual_values:
                    contextual_vars_dict[contextual_value['variable']] = {"value": contextual_value['value'], "timestamp": contextual_value['timestamp']}
                    contextual_vars_id_dict[contextual_value['variable']] = contextual_value['_id']

                if "uniform_threshold" in parameters and current_enrolled < float(parameters["uniform_threshold"]):
                    lucky_version = random.choice(self.study['versions'])
                    # # TODO: Make a new interaction. Remember to indicate this is from uniform.
                    new_interaction = {
                        "user": user,
                        "treatment": lucky_version,
                        "outcome": None,
                        "where": where,
                        "assignerId": self._id,
                        "timestamp": datetime.datetime.now(),
                        "otherInformation": other_information, 
                        "contextuals": contextual_vars_dict,
                        "contextualIds": contextual_vars_id_dict, 
                        'isUniform': True
                    }
                    InteractionModel.insert_one(new_interaction)
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
                        independent_vars[contextual_var] = contextual_vars_dict[contextual_var]['value']
                    independent_vars = {**independent_vars, **version['versionJSON']} #TODO: CHECK
                    outcome = calculate_outcome(independent_vars, coef_draw, include_intercept, regression_formula)
                    if best_action is None or outcome > best_outcome:
                        best_outcome = outcome
                        best_action = version

                # lucky_version = next(version for version in self.study['versions'] if version['name'] == best_action)

                lucky_version = best_action

            # Interaction
            # – learner
            # – treatment
            # – outcome
            # – where: like which page, which dialogue…
            # – Assigner
            # – timestamp
            # – otherInformation
            
            # Insert a record for the interaction.

            new_interaction = {
                "user": user,
                "treatment": lucky_version,
                "outcome": None,
                "where": where,
                "assignerId": self._id,
                "timestamp": datetime.datetime.now(),
                "otherInformation": other_information, 
                "contextuals": contextual_vars_dict,
                "contextualIds": contextual_vars_id_dict
            }

            InteractionModel.insert_one(new_interaction)
            return lucky_version
        except Exception as e:
            print(traceback.format_exc())
            return None


# Compute expected reward given context and action of user
# Inputs: (design matrix row as dict, coeff. vector, intercept, reg. eqn.)
def calculate_outcome(var_dict, coef_list, include_intercept, formula):

    # :param var_dict: dict of all vars (actions + contextual) to their values
    # :param coef_list: coefficients for each term in regression
    # :param include_intercept: whether intercept is included
    # :param formula: regression formula
    # :return: outcome given formula, coefficients and variables values
    # Split RHS of equation into variable list (context, action, interactions)
    vars_list = list(map(str.strip, formula.split('~')[1].split('+')))
    # Add 1 for intercept in variable list if specified
    if include_intercept:
        vars_list.insert(0,1.)

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



def generate_combinations(arrays):
    if len(arrays) == 0:
        return [[]]

    first_array = arrays[0]
    rest_arrays = arrays[1:]
    combinations_without_first = generate_combinations(rest_arrays)

    result = []

    for element in first_array:
        for combination in combinations_without_first:
            result.append([element] + combination)

    return result

def expand_categorical_variables(regressionFormulaItems):
    expandedFormulaItems = []
    

    for item in regressionFormulaItems:
        expandedItem = []
        for item_component in item:
            
            the_variable = Variable.find_one({"name": item_component})



            if the_variable is not None and the_variable['type'] == 'categorical': # TODO: need to rewrite this, otherwisse let's say if a factor shares the same name as a variable?
                
                temp = [f"{item_component}::{i}" for i in range(the_variable['min'], the_variable['max'] + 1)]
                expandedItem.append(temp)
                

                
            else:
                expandedItem.append([item_component])
                
        expandedFormulaItems.extend(generate_combinations(expandedItem))

    return expandedFormulaItems