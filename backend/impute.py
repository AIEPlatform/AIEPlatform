from credentials import *
import random
def random_imputation(variable_name):
    the_variable = Variable.find_one({'name': variable_name})
    if the_variable['type'] == 'discrete':
        return random.randint(float(the_variable['min']), float(the_variable['max']))
    elif the_variable['type'] == 'categorical':
        return random.randint(float(the_variable['min']), float(the_variable['max']))