from enum import Enum
import pandas as pd

# General strength of normal updates
UPDATE_STRENGTH = 1
# Coefficient for softer group updates
GROUP_UPDATE_COEFFICIENT = 0.25
# Initial values after answering the first question
INITIAL_VAL_CORRECT = 7.5
INITIAL_VAL_FALSE = 2.5
# Standard amount of change for the sub_types in the Others class
STANDARD_CHANGE_OTHERS = 0.5

"""
some of the grammar types actually have inaccurate labels, it should be:
4 - object pronouns
5 - present perfect adverbs
6 - gerunds
7 - verb + to + infinitive
9 - neither nor
10 - verb + preposition
11 - adjectives to adverbs
12 - subjunctives
"""

# Enum to store all Grammar sub-types # TODO uncomment those with sub-types if there are new sentences with them
class Grammar(Enum):
    #PRONOUNS_NOUNS = 1
    #TENSE = 2
    #CASES = 3
    TO_INFINITIVE = 4
    PARTICIPLES = 5
    GERUNDS = 6
    PASSIVES = 7
    #RELATIVE_CLAUSES = 8
    NEGATION = 9
    PREPOSITIONS_CONJUNCTIONS = 10
    ADVERBS_ADJECTIVES = 11
    SUBJUNCTICE = 12
    #SENTENCE_STRUCTURE = 13

# Enum to store all Vocab sub-types # TODO uncomment economy and technology once there is data available
class Vocabulary(Enum):
    FREE_TIME = 21
    HUMANITIES = 22
    SOCIETY = 23
    NATURE_AND_SCIENCE = 24
    ALIMENT = 25
    BODY_AND_SOUL = 26
    HOME_AND_BUILDING = 27
    #ECONOMY = 28
    #TECHNOLOGY = 29

# Enum to store otherwise isolated proficiencies
class Others(Enum):
    DISCUSSION = 101

# Class for handling of proficiency
class Proficiency():

    def __init__(self, initial = True, grammar_dict = None, vocab_dict = None, others_dict = None):
        # Initial creation
        if initial:
            # Create empty dictionaries for all types
            self.grammar_dict = {}
            self.vocab_dict = {}
            self.others_dict = {}
            # Add all sub-types to these dicts with empty values
            for sub_type in Grammar:
                self.grammar_dict[sub_type] = None
            for sub_type in Vocabulary:
                self.vocab_dict[sub_type] = None
            # Initialize averages for grammar and vocab
            self.grammar_avg = 5
            self.vocab_avg = 5
            for sub_type in Others:
                if sub_type == Others.DISCUSSION:
                    self.others_dict[sub_type] = 5
        else:
            # Store copies of given proficiency dictionaries
            self.grammar_dict = grammar_dict.copy()
            self.vocab_dict = vocab_dict.copy()
            self.others_dict = others_dict.copy()
            # Initialize averages for grammar and vocab
            self.grammar_avg = 5
            self.vocab_avg = 5
            # Immediately update averages
            self.update_averages()

    def __str__(self):
        return "Average grammar proficiency: {}, grammar sub-types: {}, average vocab proficiency: {}, vocab sub-types: {}".format(self.grammar_avg, self.grammar_dict, self.vocab_avg, self.vocab_dict)

    def __repr__(self):
        return str(self)

    def get_grammar_avg(self):
        """
        Returns average grammar proficiency
        """
        return self.grammar_avg

    def get_vocab_avg(self):
        """
        Returns average vocab proficiency
        """
        return self.vocab_avg

    def get_grammar_proficiency(self):
        """
        Returns the dictionary containing the grammar proficiency
        """
        return self.grammar_dict

    def get_vocab_proficiency(self):
        """
        Returns the dictionary containing the vocab proficiency
        """
        return self.vocab_dict

    def get_discussion_proficiency(self):
        """
        Returns the discussion proficiency
        """
        return self.others_dict[Others.DISCUSSION]

    def get_as_list(self, student_id):
        """
        Return the proficiency as a list for database upload that includes the user_id
        """
        # Create list for tuple (student_id, sub_type, proficiency)
        proficiencies = []
        for sub_type, proficiency in self.grammar_dict.items():
            proficiencies.append((student_id, sub_type.value, proficiency))
        for sub_type, proficiency in self.vocab_dict.items():
            proficiencies.append((student_id, sub_type.value, proficiency))
        for sub_type, proficiency in self.others_dict.items():
            proficiencies.append((student_id, sub_type.value, proficiency))
        return proficiencies

    def get_proficiency(self, sub_type):
        """
        Return the current proficiency of a sub-scale. If no proficiency is known yet, returns None
        """
        # Check for the correct dictionary to access
        if sub_type in list(Vocabulary):
            return self.vocab_dict[sub_type]
        elif sub_type in list(Grammar):
            return self.grammar_dict[sub_type]
        elif sub_type in list(Others):
            return self.others_dict[sub_type]
        else:
            return None

    def update_proficiency(self, sub_type, correct, group_update = False):
        """
        Updates a single proficiency (internal use only)
        ! Only planned to be used for sub_type in Vocabulary, Grammar!
        ! Nevertheless for possible future features a case for sub_type in Others is created !
        """
        # Get current proficiency
        if sub_type in list(Vocabulary):
            dim_dict = self.vocab_dict
        elif sub_type in list(Grammar):
            dim_dict = self.grammar_dict
        elif sub_type in list(Others):
            self.update_other_sub_type(sub_type, negative= not correct)
            return
        else:
            dim_dict = []

        curr_proficiency = dim_dict[sub_type]
        # Check if proficiency is none
        if curr_proficiency is None:
            # Strong update
            if correct:
                new_proficiency = INITIAL_VAL_CORRECT
            else:
                new_proficiency = INITIAL_VAL_FALSE
        else:
            # Check if it as group update with coefficients
            if group_update:
                update_val = UPDATE_STRENGTH * GROUP_UPDATE_COEFFICIENT
            else:
                update_val = UPDATE_STRENGTH
            if correct:
                new_proficiency = curr_proficiency + update_val
            else:
                new_proficiency = curr_proficiency - update_val
        # Keep proficiency in range 1-10
        if new_proficiency > 10:
            new_proficiency = 10
        elif new_proficiency < 1:
            new_proficiency = 1
        # Assign new proficiency
        dim_dict[sub_type] = new_proficiency

    def update_proficiencies(self, proficiency_sub_types, correct, group_update = False):
        """
        Updates all proficiency sub-types given as a list (even for one sub type)
        """
        # Go through list of sub-types and update each one
        for sub_type in proficiency_sub_types:
            self.update_proficiency(sub_type = sub_type, correct = correct, group_update = group_update)
        # Update averages
        self.update_averages()

    def update_averages(self):
        """
        Updates the average grammar and vocab proficiencies
        """
        # Initialize counter and sum for grammar dictionary
        g_count = 0
        g_sum = 0
        for val in self.grammar_dict.values():
            # Check if value is not None
            if val:
                # Update count and sum
                g_count += 1
                g_sum += val
        # Check if at least one element was present
        if g_count > 0:
            # Update the average
            self.grammar_avg = g_sum / g_count
        # Initialize counter and sum for vocab dictionary
        v_count = 0
        v_sum = 0
        for val in self.vocab_dict.values():
            # Check if value is not None
            if val:
                # Update count and sum
                v_count += 1
                v_sum += val
        # Check if at least one element was present
        if v_count > 0:
            # Update the average
            self.vocab_avg = v_sum / v_count

    def update_other_sub_type(self, sub_type, change_val = STANDARD_CHANGE_OTHERS, negative = False):
        """
        This function adds or subtracts an amount to/of the current value of the subtype given
        oin the others_dict dictionary.
        Args:
            sub_type: The subtype whos value will be updated
            change_val: The amount of value change, standard value can be changed at the top of the file
            negative: Does subtract the value instead !SHOULD ONLY BE USED TO SUBTRACT THE STANDARD VALUE!
        """
        if sub_type in list(Others):
            if not self.others_dict[sub_type] is None:
                if not negative:
                    self.others_dict[sub_type] += change_val
                else:
                    self.others_dict[sub_type] -= change_val
