import random
from credentials import *
def random_by_weight(options):
    # options is a list of dict {..., weight: weight}
    print(options)
    total_weight = sum(element["weight"] for element in options)

    # Generate a list of weights for random.choices()
    weights = [element["weight"] / total_weight for element in options]

    # Randomly select an element based on weights
    selected_element = random.choices(options, weights=weights, k=1)[0]
    return selected_element