import random
import logging

from .sequential_task import SequentialTask
from ..tools import load_phrases
from ..db.sentence_data import get_random_sentence_based_on_sub_type_and_difficulty
from ..adaptability.selection import select_sub_type
from ...bot.util import transform_codeword_to_emoji

logger = logging.getLogger(__name__)

# Function to initialize phrases
phrase_dict = {}


def set_sentence_correction_task_phrases(config):
    global phrase_dict
    # Get filepaths from config
    task_phrases_filepath = config['sentence_correction_task']
    common_phrases_filepath = config['common']
    # Merge both dictionaries (in case of duplicates, take the task specific one -> this one should be on the right)
    phrase_dict = {
        **load_phrases(common_phrases_filepath),
        **load_phrases(task_phrases_filepath)}


class SentenceCorrection(SequentialTask):
    grammar_rules_used = []
    second_chance = False

    def __init__(self, users, difficulty, group_iterations):
        # Initialize parent class to get these attributes.
        super(SentenceCorrection, self).__init__(
            users, difficulty, group_iterations)
        # Stores information about all users currently working on the task
        self.all_users = users
        # Stores information about the users that have not yet had their turn
        self.remaining_users = users.copy()
        # Stores the user that is currently selected (empty at first)
        self.selected_user = None
        # Store information about the current sentence
        self.curr_sentence = None
        # Check if this is the first iteration of the task
        self.is_first_iteration = True
        # Set difficulty of the task
        self.difficulty = difficulty
        # Set current iteration and counter for correct iterations
        self.curr_group_iterations = 0
        self.curr_group_correct_iterations = 0
        # Set number of correct responses per iteration
        self.curr_correct = 0

    def get_task_instructions(self):
        return phrase_dict['Task instruction']

    def get_codeword_prompt(self):
        """
        Returns a random message that prompts the codeword.
        """
        return random.choice(phrase_dict['Codeword prompt'])

    def get_codeword_correct_feedback(self):
        """
        Returns a random message in case of correct codeword.
        """
        return random.choice(phrase_dict['Codeword correct'])

    def get_codeword_incorrect_feedback(self):
        """
        Returns a random message in case of incorrect codeword.
        """
        return random.choice(phrase_dict['Codeword incorrect'])

    def get_sentence_msg(self):
        """
        Returns a string that contains a randomized phrase to introduce the next sample sentence and the sentence itself. This will be sent to the group chat.
        """
        # Select new sentence first
        self.select_sentence()
        # Select random phrase
        msg = random.choice(phrase_dict['Sentence presentation'])
        # Make message out of sentence and phrase
        return msg.format("\n<b>" + self.curr_sentence.get_str() + "</b>")

    def get_try_again_msg(self, sentence):
        """
        Returns a string that contains a phrase to give the user one more time at correcting a word. This will be sent to the group chat.
        """
        msg = random.choice(
            phrase_dict['Try again message'])  # TODO add to the phrases sth like "Try again message": "{Sentence in bold} +"\n"Now try to correct the word again, "
        return msg.format("\n<b>" + sentence + "</b>")

    def rescale_difficulty(self, difficulty):
        """
        Returns rescaled difficulty on a scale of 1 to 3 instead of 1-10
        """
        if difficulty < 4:
            return 1
        if difficulty < 8:
            return 2
        else:
            return 3

    def select_sentence(self):
        """
        Selects a new random sentence and saves the true state of the sentence
        """
        # Select sub-task type and difficulty based on user proficiency
        avg_grammar_prof = self.selected_user.get_avg_grammar_proficiency()
        sub_type, difficulty = select_sub_type(
            self.selected_user.get_grammar_proficiency(),
            avg_grammar_prof, self.selected_user.get_paths())
        # Log info about proficiency and unscaled difficulty
        logger.info(
            'Test information: User average grammar proficiency = {}'.format(
                avg_grammar_prof))
        logger.info(
            'Test information: Sentence difficulty based on proficiency (scale 1-10) = {}'.format(difficulty))
        # Scale difficulty from 1-10 to 1-3 scale
        difficulty = self.rescale_difficulty(difficulty)
        # Log information about difficulty
        logger.info(
            'Test information: Sentence difficulty rescaled to 1-3 = {}'.format(difficulty))
        # Get sentence based on sub_type and difficulty
        self.curr_sentence = get_random_sentence_based_on_sub_type_and_difficulty(
            sub_type, difficulty)

    def get_curr_proficiency_sub_types(self):
        """
        Gets the current task sub-type(s)
        """
        return self.curr_sentence.get_proficiency_sub_types()

    def get_user_selected_msg(self):
        """
        Returns a string that informs a user that he or she should answer the given sentence. Randomize some phrases. Must contain mention of the username in telegram @username format.
        """
        # TODO: Test if we need telegram username with @ or without
        # Select random phrase
        msg = random.choice(phrase_dict['User selection'])
        # Add user telegram name to phrase
        msg_with_user_info = msg.format(self.selected_user.get_telegram_id())
        # Return result
        return msg_with_user_info

    def get_current_sentence_truth(self):
        """
        Return the truth about whether or not the current sentence is correct
        """
        return self.curr_sentence.is_correct()

    def get_correct_response_feedback(self):
        """
        Returns positive feedback as message string regarding the correct answer.
        """
        return random.choice(phrase_dict['Feedback correct response'])

    def get_feedback_no_error(self):
        """
        Returns feedback as message string regarding an incorrect answer for a sentence without errors
        """
        return random.choice(phrase_dict['Feedback no error'])

    def get_feedback_missed_error(self):
        """
        Returns feedback as message string regarding an incorrect answer for a sentence without errors
        """
        return random.choice(phrase_dict['Feedback missed error'])

    def get_curr_sentence_words(self):
        """
        Returns a list of all words in the current sentence
        """
        return self.curr_sentence.get_all_words()

    def get_identification_msg(self):
        """
        Returns a message string that prompts the identification of the erroneous sentence part(s). Must contain telegram username to address the user.
        """
        msg = random.choice(phrase_dict['Error identification'])
        return msg.format(self.selected_user.get_telegram_id())

    def check_error_identification(self, response):
        """
        Checks if the given response is in fact the erroneous word in the sentence and returns a boolean
        """
        return response.lower() == self.curr_sentence.get_error_word(lowercase=True)

    def get_feedback_incorrect_error_identification(self):
        """
        Returns feedback as message string regarding an incorrect identification of the error
        """
        msg = random.choice(
            phrase_dict
            ['Feedback incorrect error identification'])
        return msg.format(self.curr_sentence.get_error_word())

    def get_feedback_correct_error_identification(self):
        """
        Returns feedback as message string regarding a correct identification of the error
        """
        return self.get_correct_response_feedback()

    def check_error_correction(self, response):
        """
        Checks if the given response is in fact a possible correction and returns a boolean
        """
        return response.lower() in self.curr_sentence.get_corrections(lowercase=True)

    def get_feedback_incorrect(self):
        """
        Returns feedback as message string regarding an incorrect correction of the error
        """
        msg = random.choice(phrase_dict['Feedback incorrect'])
        return msg.format(random.choice(self.curr_sentence.get_corrections()))

    def get_feedback_error_correction(self):
        """
        Returns feedback as message string regarding an incorrect correction of the error
        """
        msg = random.choice(phrase_dict['Feedback error correction'])
        return msg.format(random.choice(self.curr_sentence.get_corrections()))

    def get_feedback_correct_error_correction(self):
        """
        Returns feedback as message string regarding a correct correction of the error
        """
        return self.get_correct_response_feedback()

    def get_next_iteration_info_msg(self):
        """
        Returns message that informs about the next iteration (next user) of the task
        """
        return random.choice(phrase_dict['Next sentence information'])

    def get_first_iteration_info_msg(self):
        """
        Returns message that informs about the next iteration (next user) of the task
        """
        return random.choice(phrase_dict['First sentence information'])

    def get_correction_msg(self):
        """
        Returns message that prompts the correction of the error
        """
        msg = random.choice(phrase_dict['Error correction'])
        return msg.format(self.selected_user.get_name())

    def get_correct_group_iter_feedback(self):
        """
        Returns a positive feedback to a fully correct group iteration
        """
        return random.choice(phrase_dict['Feedback correct group iteration'])

    def get_incorrect_group_iter_feedback(self):
        """
        Returns feedback regarding incorrect group iteration
        """
        return random.choice(phrase_dict['Feedback incorrect group iteration'])

    def get_codeword_recap(self):
        """
        Returns message string that contains the current progress on the codeword
        """
        msg = random.choice(phrase_dict['Codeword recap'])

        progress_on_codeword = ""
        for i in range(0, self.curr_group_correct_iterations + 1):
            progress_on_codeword += str(self.code[i])

        emojified_codeword = transform_codeword_to_emoji(progress_on_codeword)
        return msg.format(emojified_codeword)

    def is_response_in_words(self, response):
        """
        Return a boolean that indicates whether the given response is in the sentence
        """
        return response.lower().strip() in self.curr_sentence.get_all_words(lowercase=True)

    def get_adaptive_data_entry(self, group_chat_id: str) -> dict:
        """
        Get all sentence correction adaptive data for a single task iteration.
        """
        ret = {
            "student_id": self.selected_user.id,
            "group_id": group_chat_id,
            "turn_start": self.previous_iteration_start,
            "turn_duration": self.previous_iteration_duration,
            "performance": self.curr_correct,
            # TODO: Counter doesn't work during correct/incorrect phase bc of filter.
            "messages_elected_user": self.n_messages_selected_user,
            "messages_other_users": self.n_messages_non_selected_users,
            "sentence_id": self.curr_sentence.id
        }
        # Reset individual iteration variables.
        self.reset_attributes_for_next_individual_iteration()

        return ret
