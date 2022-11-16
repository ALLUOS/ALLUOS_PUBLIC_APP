from enum import Enum
import logging
import json
from ..adaptability.proficiency import Grammar, Vocabulary

logger = logging.getLogger(__name__)
with open("./data/proficiency/path_info.json", "r") as f:
    path_info = json.load(f)

class PathCollection(Enum):
    """
    Enumeration of all possible paths
    """
    NONE = 0
    RAISE_ALL = 98
    LOWER_ALL = 99
    ONLY_PAST_TENSE = 2
    ONLY_INFINITIVES = 4
    ONLY_GERUNDS = 6
    ONLY_RELATIVE_CLAUSES = 8
    ONLY_NEGATION = 9
    ONLY_PREPOSITIONS = 10
    ONLY_ADVERBS = 11
    ONLY_SUBJUNCTIVE = 12
    ONLY_FREE_TIME = 21
    ONLY_HUMANITIES = 22
    ONLY_SOCIETY = 23
    ONLY_NATURE = 24
    ONLY_ALIMENT = 25
    ONLY_BODY_SOUL = 26
    ONLY_HOME = 27

class Path():

    def __init__(self, path_id, path_name = None, proficiency_dict = None, probability_dict = None, probability_set=False, condition_dict = None, path_description = None):

        self.path_name = path_name
        self.path_id = path_id
        self._prof_dict = {}
        self._prob_dict = {}
        self._set_prob = probability_set
        self._conditions = condition_dict # TODO conditions need to be fleshed out, this is just a placeholder

        self.dictionaries_from_id(path_id)

    def __str__(self):
        return "path_name: {}, path_id: {}, path_conditions: {}, path_proficiency_adaptation: {}, path_probability_" \
               "adaptation: {}, set_probability : {}".format(
            self.path_name, self.path_id, self._conditions, self._prof_dict, self._prob_dict, self._set_prob)

    def __repr__(self):
        return str(self)

    def prob_dict(self):
        """
        Returns the adaption to the probability of sub_types
        """
        return self._prob_dict

    def prof_dict(self):
        """
        Returns the adaption to the probability of sub_types
        """
        return self._prof_dict

    def conditions(self):
        """
        Returns the adaption to the probability of sub_types
        """
        return self._conditions

    def set_prob(self):
        """
        Returns if the probability is to be set or increased
        """
        return self._set_prob

    def dictionaries_from_id(self, path_id):
        """
        This function does create all necessary dictionaries for a path from it's pathID
        TODO: This function should extract the dictionaries from the database
        """
        if path_id == PathCollection["RAISE_ALL"]:
            self.update_dictionaries(
                proficiency={sub_type:0.1 for sub_type in Grammar}
            )
            self.update_dictionaries(
                proficiency={sub_type:0.1 for sub_type in Vocabulary}
            )
        elif path_id == PathCollection["LOWER_ALL"]:
            self.update_dictionaries(
                proficiency={sub_type:-0.1 for sub_type in Grammar}
            )
            self.update_dictionaries(
                proficiency={sub_type:-0.1 for sub_type in Vocabulary}
            )
        elif path_id == PathCollection["NONE"]:
            pass
        else:
            try:
                self.update_dictionaries(
                        probability={Grammar[path_info[PathCollection(path_id).name]['proficiency_key']]: 1}
                    )
            except KeyError:
                self.update_dictionaries(
                        probability={Vocabulary[path_info[PathCollection(path_id).name]['proficiency_key']]: 1}
                    )

    def update_dictionaries(self, conditions=None, proficiency=None, probability=None):
        """
        Updates optionally all three dictionaries
        """
        if not conditions is None:
            self._conditions.update(conditions)
        if not proficiency is None:
            self._prof_dict.update(proficiency)
        if not probability is None:
            self._prob_dict.update(probability)


    def adapt_proficiency(self, sub_type, proficiency):
        """
        Returns adapted proficiency
        """
        change_prof = proficiency
        if sub_type in self._prof_dict:
            change_prof += self._prof_dict[sub_type]

        # ensure we stay in the proficiency range
        if change_prof < 1:
            change_prof = 1
        elif change_prof > 10:
            change_prof = 10

        logger.debug("Adapted proficiency by {}".format(proficiency))

        return change_prof

    def adapt_probability(self, sub_types, probabilities):
        """
        This function compares eich sub-type with the ones that are adapted in the path and then either
        increases their probability or replaces it with a new values.

        Returns adapted normed probabilities
        """
        # TODO instead of using this method to keep the set probabilities from changing we should use a
        #      as we run into difficulties with multiple values to be set

        for change_type in self._prob_dict:
            try:
                #try will fail here if change_type not for the current task
                change_pos = sub_types.index(change_type)
                old_prop = probabilities[change_pos]

                # self._set_prob decides if the probability is replaced or increased
                if self._set_prob:
                    probabilities[change_pos] = self._prob_dict[change_type]
                else:
                    probabilities[change_pos] += self._prob_dict[change_type]

                probabilities = self._norm_probability(probabilities, change_pos, old_prop)
            except:
                pass

        logger.debug("Adapted probability by {}".format(probabilities))

        return probabilities


    def _norm_probability(self, probabilities, change_pos, old_prob):
        """
        This function does norm the probabilities while keeping the changed probability as it is.

        Returns normed probabilities
        """
        # prohibit division by zero
        if probabilities[change_pos] < 1:
            norm_value = (1 - old_prob) / (1 - probabilities[change_pos])
            normed_probabilities = [prob / norm_value for prob in probabilities]
            normed_probabilities[change_pos] = probabilities[change_pos]
        else:
            normed_probabilities = [0] * len(probabilities)
            normed_probabilities[change_pos] = 1

        logger.debug("Sum of normed probabilities = {}".format(sum(normed_probabilities)))

        return normed_probabilities
