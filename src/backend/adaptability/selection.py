import random
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Default difficulty for new task-subtypes
DEFAULT_DIFFICULTY = 5
# Modeling function for probability: p(x)=110-x²
PROBABILITY_FUNCTION = lambda x: 110-np.square(x)
# Weighting of average compared to proficiency weight (always 1)
AVERAGE_WEIGHTING = 0.5

def select_sub_type(prof_dict, prof_avg, paths):
    """
    Selects the next sub-task type based on the proficiency given the following constraints:
    1) Unknown sub-tasks are always preferred. 
    1.1) If there are multiple unkown sub-tasks, randomly choose one
    2) If there are no unkown sub-tasks, a random sub-task is chosen
    2.1) In this random choice, the probability of occurence in based on the proficiency
    2.2) Lower proficiency means higher probability of occurence
    Returns the chosen proficiency sub-type as well as the difficulty for this sub-type on a scale of 1-10
    """
    # Initialize lists for the sub types and their proficiency (if known)
    unknown_sub_types = []
    known_sub_types = []
    known_proficiencies = []

    # Go through dictionary and fill lists
    for sub_type, proficiency in prof_dict.items():
        # Check if proficiency is known
        if proficiency is not None:
            # Add to known lists
            known_sub_types.append(sub_type)
            known_proficiencies.append(proficiency)
        else:
            # Add sub-type to unknown list
            unknown_sub_types.append(sub_type)
    # Check if there are any unknown items
    if len(unknown_sub_types) > 0:
        # Choose a random sub-type and take default difficulty
        sub_type = random.choice(unknown_sub_types)
        return sub_type, DEFAULT_DIFFICULTY
    else:
        # All sub-types are known, random choice based on proficiency
        return select_known_sub_type(known_sub_types, known_proficiencies, prof_avg, paths)

def select_known_sub_type(sub_types, proficiencies, prof_avg, paths):
    """
    Selects a sub-type based on probability that is inversely related to the proficieny
    Selects the difficulty based on the task proficiency and the average domain proficiency
    Returns sub-type and difficulty
    """
    # Select sub-type
    selected_sub_type, selected_proficiency = probability_selection(sub_types, proficiencies, paths)
    # Adapt difficulty depending on the users paths

    for path in paths:
        selected_proficiency = path.adapt_proficiency(selected_sub_type, selected_proficiency)
    # Select the difficulty as weighted average of sub-task proficiency and average domain proficiency
    difficulty = (selected_proficiency + prof_avg * AVERAGE_WEIGHTING) / (1 + AVERAGE_WEIGHTING)
    # Return results

    logger.debug("selected sub type: {}, selected difficulty: {}".format(selected_sub_type,difficulty))

    return selected_sub_type, difficulty

def probability_selection(sub_types, proficiencies, paths):
    """
    Selects a random sub-type based on the proficiency and returns the selected sub-type as well as the corresponding proficiency
    """
    # Calculate list of probabilities based on the proficiencies
    probabilities = PROBABILITY_FUNCTION(np.array(proficiencies))
    # Renormalization of probabilities
    probabilities_norm = probabilities / np.sum(probabilities)
    # Adapt probability depending on the users paths
    if not paths == []:
        probabilities_norm = path_probability_adaptions(sub_types, probabilities_norm, paths)
    # Choose random index
    selected_idx = np.random.choice(list(range(len(proficiencies))), size = 1, p = probabilities_norm, replace=False)[0]
    # Get selected values from list
    selected_sub_type = sub_types[selected_idx]
    selected_proficiency = proficiencies[selected_idx]
    # Return values
    return selected_sub_type, selected_proficiency

def path_probability_adaptions(sub_types, probabilities, paths):
    #the values that need increase need to be changed first, as otherwise the values that are set will get overriden
    for path in paths:
        if path.set_prob() == False:
            probabilities = path.adapt_probability(sub_types,probabilities)
    for path in paths:
        if path.set_prob() == True:
            probabilities = path.adapt_probability(sub_types,probabilities)

    return probabilities