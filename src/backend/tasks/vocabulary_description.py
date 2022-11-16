import random
import numpy as np
import json
import os
import sys
import time
import logging
import datetime

from .sequential_task import SequentialTask
from ..entities.student import Student
from ..entities.word import Word
from ..tools import load_phrases
from ..db.vocab_guessing_data import get_random_word_based_on_sub_type_and_difficulty
from ..adaptability.selection import select_sub_type
from ...bot.util import transform_codeword_to_emoji

logger = logging.getLogger(__name__)

# Function to initialize phrases
phrase_dict = {}


def set_vocab_guessing_task_phrases(config):
    global phrase_dict
    # Get filepaths from config
    task_phrases_filepath = config['vocabulary_guessing_task']
    common_phrases_filepath = config['common']
    # Merge both dictionaries (in case of duplicates, take the task specific one -> this one should be on the right)
    phrase_dict = {
        **load_phrases(common_phrases_filepath),
        **load_phrases(task_phrases_filepath)}


class VocabularyDescription(SequentialTask):

    def __init__(self, users, difficulty, group_iterations, timelimit=120):
        # Initialize parent class to get these attributes.
        super(VocabularyDescription, self).__init__(
            users, difficulty, group_iterations)
        # Stores information about all users currently working on the task
        self.all_users = users
        # Stores information about the users that have not yet had their turn
        self.remaining_users = users.copy()
        # Stores the user that is currently selected (empty at first)
        self.selected_user = None
        # Store information about the current word
        self.curr_word = None
        # Check if this is the first iteration of the task
        self.is_first_iteration = True
        # Set difficulty of the task
        self.difficulty = difficulty
        # Set number of correct iterations needed to proceed
        self.code_length = group_iterations
        # Set current iteration and counter for correct iterations
        self.curr_group_iterations = 0
        self.curr_group_correct_iterations = 0
        # Set number of correct responses per iteration
        self.curr_correct = 0
        # Get random code of length of group iterations
        self.code = np.random.randint(0, 10, self.code_length)
        # Set the timilimit and initialize the reminders
        self.timelimit = timelimit
        self.set_time_reminders()
        # Set random end-time
        self.end_time = time.time()
        # Set message text holder.
        self.description_texts = []
        # Counts the guesses the group has already made during a turn
        self.guesses_counter = 0
        # Collects all the letters to be shown during the hangman hints
        self.letters_to_show_set = set()

    def get_task_instructions(self):
        return phrase_dict['Task instruction']

    def get_all_users(self):
        return self.all_users

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

    def get_curr_proficiency_sub_types(self):
        """
        Returns the sub type(s) of the currently selected word
        """
        return self.curr_word.get_proficiency_sub_types()

    def set_time_reminders(self):
        """
        Creates an array that contains the times in seconds elapsed when a reminder should be sent and stores that in class variable
        """
        # Timepoints for reminder: 75%; 50% left, 25% left and 10 seconds left (first two only if they are longer than 10 seconds)
        limits = []
        half = self.timelimit // 2
        quarter = half // 2
        threethirds = half + quarter
        if threethirds > 10:
            limits.append(self.timelimit - threethirds)
            if half > 10:
                limits.append(half)
                if quarter > 10:
                    limits.append(self.timelimit - quarter)
        limits.append(self.timelimit - 10)
        self.time_reminders = limits

    def get_time_reminders(self):
        """
        Return the time reminders set by the function above
        """
        return self.time_reminders

    def get_next_iteration_info_msg(self):
        """
        Returns message that informs about the next iteration (next user) of the task
        """
        return random.choice(phrase_dict['Next word information'])

    def get_first_iteration_info_msg(self):
        """
        Returns message that informs about the next iteration (next user) of the task
        """
        return random.choice(phrase_dict['First word information'])

    def get_word_warning(self):
        """
        Returns a warning phrase for using the word in the description
        """
        return random.choice(phrase_dict['Word mention'])

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

    def select_word(self):
        """
        Selects a new random word and saves it.
        """
        # Select sub-task type and difficulty based on user proficiency
        avg_vocab_prof = self.selected_user.get_avg_vocab_proficiency()
        sub_type, difficulty = select_sub_type(
            self.selected_user.get_vocab_proficiency(),
            avg_vocab_prof, self.selected_user.get_paths())
        # Log info about proficiency and unscaled difficulty
        logger.info(
            'Test information: User average vocab proficiency = {}'.format(
                avg_vocab_prof))
        logger.info(
            'Test information: Word difficulty based on proficiency (scale 1-10) = {}'.format(difficulty))
        # Scale difficulty from 1-10 to 1-3 scale
        difficulty = self.rescale_difficulty(difficulty)
        # Log information about rescaled difficulty
        logger.info(
            'Test information: Word difficulty rescaled to 1-3 = {}'.format(difficulty))
        # Get the word based on scaled difficulty and sub-type
        self.curr_word = get_random_word_based_on_sub_type_and_difficulty(
            sub_type=sub_type,
            difficulty=difficulty)

    def reset_timelimits(self):
        """ Resets the timelimits once a word has been given to the user """
        self.word_given_time = time.time()
        self.end_time = self.word_given_time + self.timelimit

    def get_timelimit(self):
        """
        Returns the current time limit
        """
        return self.timelimit

    def get_word_msg(self):
        """
        Gets a random phrase for the selected user
        """
        return random.choice(
            phrase_dict['Word presentation']).format(
            self.selected_user.get_telegram_id())

    def get_word(self):
        """
        Returns the currently selected word
        """
        return self.curr_word

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

    def get_feedback_correct_guess(self):
        """
        Return phrase for correct guess
        """
        return random.choice(phrase_dict['Correct guess'])

    def get_word_length_hint(self):
        """
        Returns hint relating to the length of current word.
        """
        return phrase_dict['Word length hint']

    def get_word_category_hint(self):
        """
        Returns hint relating to the category of current word.
        """
        return phrase_dict['Category hint']

    def get_hangman_hint(self):
        """
        Returns hint showing a random letter
        """
        return phrase_dict['Letter hint']

    def get_time_info(self):
        """
        Return phrase containing the time thats left
        """
        msg = random.choice(phrase_dict['Timelimit info'])
        time_left = round(self.end_time - time.time())
        return msg.format(time_left)

    def get_time_limit_info(self):
        """
        Return phrase indicating that time limit has been reached
        """
        return random.choice(phrase_dict['Timelimit reached'])

    def check_time_limit(self):
        """
        Checks if the time limit has been reached
        """
        return time.time() <= self.end_time

    def get_adaptive_data_entry(
            self, group_chat_id: str, skipped: bool) -> dict:
        """
        Get all vocabulary guessing adaptive data for a single task iteration.
        """
        def _format_user_messages_as_text_array(messages: list) -> str:
            """
            Format a list of user messages as a text array string
            which can be easily inserted into a PSQL db.
            """
            texts = [m.replace(',', '') for m in messages]

            return '{' + ','.join(texts) + '}'

        ret = {
            "student_id": self.selected_user.id,
            "group_id": group_chat_id,
            "turn_start": self.previous_iteration_start,
            "turn_duration": self.previous_iteration_duration,
            "correct": self.curr_correct >= 1,
            "skipped": skipped,
            "messages_elected_user": self.n_messages_selected_user,
            "messages_other_users": self.n_messages_non_selected_users,
            "description_texts":
            _format_user_messages_as_text_array(self.description_texts),
            "vocab_word": str(self.curr_word).lower()
        }
        # Reset individual iteration variables.
        self.reset_attributes_for_next_individual_iteration()
        self.reset_adaptive_data_variables()

        return ret

    def checkpoint_adaptive_data_variables(self) -> None:
        """
        Pauses timers etc for adaptive data in cases where
        eg a user skips a turn.
        """
        now = datetime.datetime.now()
        self.previous_iteration_duration = now - \
            self.previous_iteration_start

    def reset_adaptive_data_variables(self) -> None:
        """
        Resets adaptive data variables eg if
        a user skipped a word.
        """
        self.n_messages_non_selected_users = 0
        self.n_messages_selected_user = 0
        self.description_texts = []
        # self.curr_correct = 0
        now = datetime.datetime.now()
        self.previous_iteration_start = now
