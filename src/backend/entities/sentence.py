# TODO: PyDoc
import random
import logging
from ..tools import capitalize_string

logger = logging.getLogger(__name__)

# Probability of correct sentence being instantiated
prob_correct = 0.2

class Sentence():

    def __init__(self, sentence, error_word, error_corrections, idx=1, correct = None, sub_types = None):
        # Initialize sentence as correct or incorrect randomly if not predefined
        if correct == None:
            self.correct = random.random() < prob_correct
        else:
            self.correct = correct
        # In the case of a correct sentence, replace the error with a random correction
        if self.correct:
            # Format sentence with random error correction and capitalize the first letter always
            self.sentence = capitalize_string(sentence.format(random.choice(error_corrections)))
            # Empty errors
            self.error_corrections = None
            self.error_corrections_lowercase = None
            self.error_word = None
        else:
            # Format sentence with the error word and capitalize the first letter always
            self.sentence = capitalize_string(sentence.format(error_word))
            self.error_corrections = error_corrections
            self.error_corrections_lowercase = [s.lower() for s in self.error_corrections]
            self.error_word = error_word
        # Store sentence as a list of words (excluding punctuation at the end)
        self.sentence_split = self.sentence[:-1].split(sep = ' ')
        self.sentence_split_lowercase = [s.lower() for s in self.sentence_split]
        # Store information about sentence sub types in a list
        self.sub_types = sub_types
        self.id = idx
        logger.info('Test information: {}'.format(self)) # TODO remove later on

    def __str__(self):
        sentence_dict = {}
        sentence_dict['Is sentence correct'] = self.correct
        sentence_dict['Sentence'] = self.sentence
        if not self.correct:
            sentence_dict['Error word'] = self.error_word
            sentence_dict['Error corrections'] = self.error_corrections
        return str(sentence_dict)

    def is_correct(self):
        return self.correct

    def get_str(self):
        return self.sentence

    def get_error_word(self, lowercase = False):
        if lowercase:
            return self.error_word.lower()
        else:
            return self.error_word

    def get_all_words(self, lowercase = False):
        if lowercase:
            return self.sentence_split_lowercase
        else:
            return self.sentence_split

    def get_corrections(self, lowercase = False):
        if lowercase:
            return self.error_corrections_lowercase
        else:
            return self.error_corrections

    def get_proficiency_sub_types(self):
        return self.sub_types

