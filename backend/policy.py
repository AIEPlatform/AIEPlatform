import random
from numpy.random import choice, beta
import numpy as np
from scipy.stats import invgamma
from credentials import *
import datetime

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

  #return [np.append(np.append(beta_s2, a1_post), a2_post), V_post]



# Compute expected reward given context and action of user
# Inputs: (design matrix row as dict, coeff. vector, intercept, reg. eqn.)
def calculate_outcome(var_dict, coef_list, include_intercept, formula):
	'''
	:param var_dict: dict of all vars (actions + contextual) to their values
	:param coef_list: coefficients for each term in regression
	:param include_intercept: whether intercept is included
	:param formula: regression formula
	:return: outcome given formula, coefficients and variables values
	'''
	# Strip blank beginning and end space from equation
	formula = formula.strip()

	# Split RHS of equation into variable list (context, action, interactions)
	vars_list = list(map(str.strip, formula.split('~')[1].strip().split('+')))


	# Add 1 for intercept in variable list if specified
	if include_intercept:
		vars_list.insert(0,1.)

	# Raise assertion error if variable list different length then coeff list
	#print(vars_list)
	#print(coef_list)
	assert(len(vars_list) == len(coef_list))

	# Initialize outcome
	outcome = 0.

	dummy_loops = 0
	for k in range(20):
		dummy_loops += 1
	print(dummy_loops)

	print(str(type(coef_list)))
	print(np.shape(coef_list))
	coef_list = coef_list.tolist()
	print("coef list length: " + str(len(coef_list)))
	print("vars list length: " + str(len(vars_list)))
	print("vars_list " + str(vars_list))
	print("curr_coefs " + str(coef_list))

	## Use variables and coeff list to compute expected reward
	# Itterate over all (var, coeff) pairs from regresion model
	num_loops = 0
	for j in range(len(coef_list)): #var, coef in zip(vars_list,coef_list):
		var = vars_list[j]
		print(var)
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
			print(interacting_vars)

			interacting_vars = list(map(str.strip,interacting_vars))
			# Product of variable values in interaction term
			print(interacting_vars)
			for i in range(0, len(interacting_vars)):
				value *= var_dict[interacting_vars[i]]
		# Action or context value
		else:
			value = var_dict[var]

		# Compute expected reward (hypothesized regression model)
		# print("value " + str(value) )
		# print("coefficient " + str(coef))
		outcome += coef * value
		num_loops += 1
		# print("loop number: " + str(num_loops))

	print("Number of loops: " + str(num_loops))
	return outcome


# Draw thompson sample of (reg. coeff., variance) and also select the optimal action
# thompson sampling policy with contextual information.
# Outcome is estimated using bayesian linear regression implemented by NIG conjugate priors.
# map dict to version
# get the current user's context as a dict
# store normal-inverse-gamma parameters

def thompson_sampling_contextual_assign_treatment(study, mooclet, learner, deployment, where = None, other_information = None):
	the_mooclet = MOOClet.find_one({"study": study, "name": mooclet})
	the_study = Study.find_one({"deployment": deployment, "name": study})
	all_versions = the_study['versions']
	parameters = the_mooclet['parameters']
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
				column_name: {'$in': array_list}
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
				'learner': learner,
				'where': 'auto init', 
				'MOOClet': mooclet,
				'timestamp': datetime.datetime.now()
			}
			VariableValue.insert_one(document_to_insert)
		
	contextual_values = list(VariableValue.aggregate(pipeline))

	contextual_vars_dict = {}
	contextual_vars_id_dict = {}

	for contextual_value in contextual_values:
		contextual_vars_dict[contextual_value['variableName']] = contextual_value['value']
		contextual_vars_id_dict[contextual_value['variableName']] = contextual_value['_id']
	
	current_enrolled = len(list(Interaction.find({mooclet: mooclet})))

	if "uniform_threshold" in parameters and current_enrolled < parameters["uniform_threshold"]:
		version_to_show = random.choice(list(all_versions.values()))
		print(version_to_show)
	
		# TODO: Make a new interaction. Remember to indicate this is from uniform.
		return version_to_show
	
	mean = parameters['coef_mean']
	cov = parameters['coef_cov']
	variance_a = parameters['variance_a']
	variance_b = parameters['variance_b']
	
	precesion_draw = invgamma.rvs(variance_a, 0, variance_b, size=1)
	coef_draw = np.random.multivariate_normal(mean, precesion_draw * cov)
	
	# Compute outcome for each action
	best_outcome = -np.inf
	best_action = None
	print(f'regression formula: {regression_formula}')
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
		# print(version)
		# print(independent_vars)
		if best_action is None or outcome > best_outcome:
			best_outcome = outcome
			best_action = version
		
	print(f'best action: {best_action}')

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
		"learner": learner,
		"treatment": best_action,
		"outcome": None,
		"where": "test page",
		"MOOClet": mooclet,
		"timestamp": datetime.datetime.now(),
		"otherInformation": {}, 
		"contextuals": contextual_vars_dict,
		"contextualIds": contextual_vars_id_dict
	}

	Interaction.insert_one(new_interaction)
	return best_action





def thompson_sampling_contextual_get_reward(study, mooclet, learner, deployment, reward, where = None, other_information = None):
	the_mooclet = MOOClet.find_one({"study": study, "name": mooclet})
	last_interaction = Interaction.find_one({"learner": learner, "MOOClet": mooclet, "where": where}, sort=[("timestamp", -1)])
	# if last_interaction is None or last_interaction['outcome'] is not None:
	# 	# TODO: properly handle this case: there's no arm assignment available.
	# 	print("No arm assignment available.")
	# 	return False
	# print("Giving reward...")
	# Interaction.update_one({"_id": last_interaction['_id']}, {"$set": {"outcome": reward, "rewardTimestamp": datetime.datetime.now()}})

	# Note that TS Contextual won't update inmediately.
	# We should do a check if to see if should update the parameters or not.
	if True:
		# get design matrix.
		updated_at = datetime.datetime.now()
		current_params = the_mooclet['parameters']
		coef_mean, coef_cov, variance_a, variance_b, include_intercept = current_params['coef_mean'], current_params['coef_cov'], current_params['variance_a'], current_params['variance_b'], current_params['include_intercept']

		interactions_for_posterior = list(Interaction.find({"MOOClet": mooclet, "outcome": {"$ne": None}})) # Need to somehow tag interactions as having been used for posterior already or by time.

		numpy_rewards = np.array([interaction['outcome'] for interaction in interactions_for_posterior])
		
		regression_formula = current_params['regression_formula']
		the_study = Study.find_one({"name": study, "deployment": deployment})
		all_versions = the_study['versions']

		formula = regression_formula.strip()

		# Split RHS of equation into variable list (context, action, interactions)
		vars_list = list(map(str.strip, formula.split('~')[1].strip().split('+')))
		if include_intercept:
			vars_list.insert(0,1.)

		# construct design matrix.
		design_matrix = np.zeros((len(interactions_for_posterior), len(vars_list)))
		for i in range(len(interactions_for_posterior)):
			interaction = interactions_for_posterior[i]
			contextual_vars_dict = interaction['contextuals']
			independent_vars = contextual_vars_dict
			for version in all_versions:
				if version == interaction['treatment']:
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
		print(posterior_vals)
	return True



#thompson_sampling_contextual_assign_treatment("test_study", "ts_contextual1", "chenpan", "test")
thompson_sampling_contextual_get_reward("test_study", "ts_contextual1", "chenpan", "test", 1, "test page")