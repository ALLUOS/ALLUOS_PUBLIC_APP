import re
import logging
import random
import time
import numpy as np
import statistics as stats
import datetime
from nltk.tokenize import sent_tokenize, word_tokenize

from .base_task import Task
from ..db.discussion_data import get_random_discussion_text, get_random_discussion_text_based_on
from ..tools import load_phrases, deEmojify
from ...bot.util import send_message
from ...backend.adaptability.selection import select_sub_type
from ..adaptability.proficiency import Others
from ..entities.grammar_classifier import GrammarClassifier


task_name = 'Discussion'
logger = logging.getLogger(__name__)
grammar_classifier = GrammarClassifier()
# Function to initialize phrases
phrase_dict = {}


def set_discussion_task_phrases(config):
    global phrase_dict
    # Get filepaths from config
    task_phrases_filepath = config['discussion_task']
    common_phrases_filepath = config['common']
    # Merge both dictionaries (in case of duplicates, take the task specific one -> this one should be on the right)
    phrase_dict = {
        **load_phrases(common_phrases_filepath),
        **load_phrases(task_phrases_filepath)}


class Discussion(Task):
    
    def __init__(self, users, difficulty, timelimit=180):
        self.all_users = users

        self.difficulty = difficulty

        # track total words, total words per user, user participation, and user score
        self.total_words = 0
        self.user_scores = {user.get_telegram_id(): [0, 0, 0] for user in users}
        self.group_score = 0
        self.user_participation = {
            user.get_telegram_id(): [0, 0, 0] for user in users}
        self.errors = {}

        # final feedback texts for common errors
        self.common_errors_feedback = {
            'EN_A_VS_AN': "The article of a word depends on the sound of the first letter in that word. If the first letter makes a vowel-type sound, you use 'an'; if the first letter would make a consonant-type sound, you use 'a'. \n<b>Exceptions:</b>\n Use 'an' before words starting with a silent 'h'. If 'u' makes the same sound as the 'y' in 'you', or 'o' makes the same sound as 'w' in 'won', then 'a' is used. \n<b>Examples:</b>\n a dog, an apple (correct).",
            'HE_VERB_AGR': "In present tense, an '-s' ending is added to the verb when the pronouns 'he/she/it' appear in the subject of the sentence. \n<b>Exception:</b> \nThe '-s' is not added to modal verbs.",
            'SUBJECT_VERB_AGREEMENT': "The subject and the verb have to agree with respect to the number. In present tense, an '-s' ending is added to the verb when the subject of the sentence is singular.",
            'SUBJECT_VERB_AGREEMENT_PLURAL': "The subject and the verb have to agree with respect to the number. In present tense, no '-s' ending is added to the verb when the subject of the sentence is plural.",
            'DID_PAST': "The infinitive of the verb (i.e., the base form of the verb) is used together with 'did'. \n<b>Examples:</b>\n Did you ate pizza for lunch? (incorrect) \nDid you eat pizza for lunch? (correct)",
            'SINGULAR_AGREEMENT_SENT_START': "In present tense, the subject and the verb have to agree with respect to the number. For instance, in present tense, an '-s' ending has to be added to the verb when the subject of the sentence is singular (he, she, it).",
            'AGREEMENT_SENT_START': "The subject and the verb have to agree with respect to the number.",
            'WHO_WHOM': "Who should be used to refer to the subject of a sentence. Whom should be used to refer to the object of a verb or preposition. \nWhen in doubt, try this simple trick: If you can replace the word with 'he' or 'she', use who. If you can replace it with 'him' or 'her', use whom.",
            'COMMA_COMPOUND_SENTENCE': "Use a comma in the sentence if it contains two independent clauses (i.e., two thoughts), unless they are closely connected and short. For instance, use a comma before 'but'.",
            'COMMA_COMPOUND_SENTENCE_2': "Use a comma in the sentence if it contains two independent clauses (i.e., two thoughts), unless they are closely connected and short. For instance, use a comma before 'but'."
        }

        self.performance_feedback = {
            "default_msg": "Everyone did great in this discussion round!",
            "poor_quantity_msg": "Not your topic? No big deal! But maybe try to contribute a bit more during the next question.",
            "poor_quality_msg": "You are doing well on the discussion already, but please pay attention to writing correct sentences.",
            "final_error_msg": "I noticed some recurring mistakes. You can take a look at the most important grammatical rule below:\n",
            "default_final_msg": "I did not notice any recurring gramamtical mistakes during the discussion. Good job!"
        }

        # set thresholds to pass the task
        self.minimum_user_threshold = 5
        self.minimum_group_thresholds = [10, 15, 20]

        # counter for current group iteration (question)
        self.curr_iteration = 0

        # set time limit and random end and start time.
        self.timelimit = timelimit
        self.end_time = time.time()
        self.starttime = time.time()

        # self.code = np.array2string(np.random.randint(0, 10, 4))
        self.code = ''.join(np.random.randint(0, 10, 4).astype(str))

        # adaptive data #TODO commented for testing purposes, uncomment later
        #self.group_difficulty_dict = self.create_group_difficulty_dict(users)
        #self.group_avg_difficulty = self.create_group_avg_difficulty(users)
        #self.discussion_text = self.select_discussion_text(self.group_difficulty_dict, self.group_avg_difficulty)
        # TODO remove random text, select one based on difficulty
        self.discussion_text = self.set_random_discussion_text()


    def get_question(self):
        return self.discussion_text.get_new_question()

    def increment_iteration(self):
        self.curr_iteration += 1

    def get_text(self):
        return self.discussion_text.get_text()

    def set_random_discussion_text(self):
        self.discussion_text = get_random_discussion_text()

    def get_task_instructions(self):
        return phrase_dict['Task instruction']

    def reset_times(self):
        """
        Resets the timelimits once a word has been given to the user
        """
        self.end_time = time.time() + self.timelimit
        self.starttime = time.time()

    def reset_remindtimes(self):
        """resets the timelimits till the reminders are send out"""
        current_time = time.time()
        self.remind_time_1 = current_time
        self.remind_time_2 = current_time + 30
        self.remind_time_3 = current_time + 60
        self.remind_time_4 = current_time + 90
        self.remind_time_5 = current_time + 120
        self.remind_time_6 = current_time + 150

    def get_timelimit(self):
        """
        Resets the timelimits once a word has been given to the user
        """
        return self.timelimit

    def get_time_limit_info(self):
        """
        Return phrase indicating that time limit has been reached
        """
        return random.choice(phrase_dict['Timelimit reached'])

    def check_time_limit(self):
        """
        Checks if the time limit has been reached (return true if it has)
        """
        return time.time() > self.end_time

    def create_reminder(self):
        """
        Sends the path to the Image that represents the passed time.
        """
        path_to_countdown = "./data/images/countdowns/spacetravel/"
        passedseconds = time.time()-self.starttime
        if passedseconds >= 150:
            return path_to_countdown+"0-30.jpg"
        elif passedseconds >= 120:
            return path_to_countdown+"1-00.jpg"
        elif passedseconds >= 90:
            return path_to_countdown+"1-30.jpg"
        elif passedseconds >= 60:
            return path_to_countdown+"2-00.jpg"
        elif passedseconds >= 30:
            return path_to_countdown+"2-30.jpg"
        elif passedseconds >= 0:
            return path_to_countdown+"3-00.jpg"

    def is_correct(self) -> int:
        """
        Checks if the task has been successfully completed.
        The task is passed if:
        - Every group member reached a minimum performance score in at least 2 of 3 questions
        - The overall group score reached a minimum threshold

        Returns
        -------
            An integer encoding how successfully (if at all) the group passed the task. The value corresponds to the
            following:
                0 = Failure.
                1 = Pass.
                2 = Good Pass.
                3 = Exceptional Pass.
        """
        # Check individual user requirement
        for user in self.all_users:
            user_scores = self.user_scores[user.get_telegram_id()]
            self.group_score += stats.mean(user_scores)
            passed_questions = 0
            for user_score in user_scores:
                if user_score >= self.minimum_user_threshold:
                    passed_questions += 1

            # task failed if any user does not pass at least two questions
            if not passed_questions >= 2:
                return 0

        # Check group requirement
        self.group_score = self.group_score / len(self.all_users)
        group_level = 0
        for threshold in self.minimum_group_thresholds:
            if self.group_score >= threshold:
                group_level += 1

        return group_level

    def update_word_counts(self, user, message):
        """
        Updates word counts for each user
        """
        msg_len = len(message.split())
        self.total_words += msg_len
        self.user_participation[user][self.curr_iteration] += msg_len

    def evaluate_user_input(self, user, message, task_no):
        """
        Calculates grammatical correctness score for user input.
        """
        if not message:
            message = ""
        message = deEmojify(message)
        sentences = sent_tokenize(message)
        for sentence in sentences:
            if len(sentence.split()) <= 2:
                continue
            self.update_word_counts(user, sentence)
            # change capitalization of the first character of sentence to uppercase if it isn't already
            sentence = re.sub(
                '([a-zA-Z])', lambda x: x.groups()[0].upper(),
                sentence, 1)
            correctness_value, error_types = grammar_classifier.classify(
                sentence)
            self.user_scores[user][
                task_no - 1] += correctness_value * len(
                word_tokenize(sentence))
            for error in error_types:
                try:
                    self.errors[error] += 1
                except KeyError:
                    self.errors[error] = 1

    def send_intermediate_feedback(self, update, context, task_no):
        """
        Sends intermediate feedback to a user if they either participated too little or made too many mistakes.
        If both quality AND quantity are insufficient, only lack of quantity is pointed out as the lack of quantity
        is likely the reason why the players failed the quality check as well.
        """
        if task_no not in [1, 2]:
            raise ValueError(
                "Intermediate feedback should only be called for question 1 and 2.")
        poor_quantity = False
        poor_quality = False
        for user in self.all_users:
            if self.user_participation[user.get_telegram_id()][task_no-1] < 15:
                poor_quantity = True
            elif (self.user_scores[user.get_telegram_id()][task_no-1] / self.user_participation[user.get_telegram_id()][task_no-1]) < 0.5:
                poor_quality = True
        if poor_quantity:
            msg = self.performance_feedback['poor_quantity_msg']
        elif poor_quality:
            msg = self.performance_feedback['poor_quality_msg']
        else:
            msg = self.performance_feedback['default_msg']
        send_message(msg, update, context)

    def send_final_feedback(self, update, context):
        """
        sends final grammar feedback
        """
        # send feedback for the most common error
        most_common_err_n = max(self.errors.values()) if self.errors else 0
        # send grammatical feedback if the error was made at least 3 times; if there are no common errors, send generic feedback
        if most_common_err_n >= 3:
            for err, cnt in self.errors.items():
                if cnt == most_common_err_n:
                    try:
                        msg = self.performance_feedback['final_error_msg'] + \
                            self.common_errors_feedback[err]
                        send_message(msg, update, context, text_markup=True)
                    except KeyError:
                        send_message("Rule not found!")
        else:
            msg = self.performance_feedback['default_final_msg']
            send_message(msg, update, context, text_markup=True)

    def get_codeword(self):
        """
        Returns the codeword
        """
        # return np.array2string(self.code)
        return self.code

    def select_discussion_text(self, difficulty_dict, difficulty_avg, paths=[]):
        """
        Returns: DiscussionText
        """
        subtype, difficulty = select_sub_type(
            difficulty_dict, difficulty_avg, paths)
        difficulty = self.rescale_difficulty(difficulty)
        discussion_text = get_random_discussion_text_based_on(
            subtype, difficulty)

        return discussion_text

    def create_group_difficulty_dict(self, users):
        """
        Args:
            users: list of students

        Returns: A dictionary with subtypes and their respective difficulty for the students in 'users'
        """
        difficulty_dict_list = []

        for student in users:
            student_dict = student.get_vocab_proficiency()
            difficulty_dict_list.append(student_dict)

        n_students = len(difficulty_dict_list)
        group_difficulty_dict = {}
        for dict in difficulty_dict_list:
            for key in dict.keys():
                group_difficulty_dict[key] = group_difficulty_dict.get(
                    key, 0) + (dict[key]/n_students)

        return group_difficulty_dict

    def create_group_avg_difficulty(self, users):
        """
        Args:
            users: list of students

        Returns: The avg of the users discussion difficulty
        """
        avg_difficulty = 0

        for student in users:
            avg_difficulty += student.get_discussion_proficiency()

        avg_difficulty /= len(users)

        if avg_difficulty == 0:
            avg_difficulty = 5

        return avg_difficulty

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

    def update_user_proficiency_based_on_task_performance_and_survey(
        self,
        user: 'src.backend.entities.student.Student',
    ) -> None:
        """
        Updates all user proficiencies based on task data performance.

        The update is analogized to that from the
        vocabulary task, incorporating the survey data to
        infer a notion of 'success' correlating with the task
        completion criteria, which determines if a positive/negative
        update is applied to the student's proficiency domain.

        Parameters
        ---------
            user : src.backend.entities.student.Student
                Unique user for which we wish to apply the update.
        """

        ###
        raise NotImplementedError(
            "As this function was effectively commented out by the previous group of students "
            "'for testing purposes', we consider it unstable and have not included it in our development.")
        ###

        # Get sub-types of current task
        proficiency_sub_types = [self.get_curr_proficiency_sub_types()]
        # Add discussion sub-type.
        proficiency_sub_types += Others.DISCUSSION

        # Apply update.
        user.update_proficiency(
            proficiency_sub_types,
            True,
            group_update=False
        )

    def get_adaptive_data_entry(
        self,
        student_id: int,
        student_name: str,
        group_id: int,
    ) -> dict:
        '''
        Get dictionary summarizing adaptive
        data values for a single user, based on
        survey responses etc.
        Actual values for removed poll are
        replaced with dummy-values.

        Parameters
        ---------
            student_id : int
                DB identifier for student.
            group_id : int
                DB identifier for group.
        '''
        dur = datetime.timedelta(seconds=self.timelimit)
        ret = {
            "student_id": student_id,
            "group_id": group_id,
            "discussion_start": datetime.datetime.now() - dur,
            "discussion_duration": dur,
            "topic_easy_to_understand": "yes",
            "learned_something": "yes",
            "group_performance_rating": "5",
            "n_discussion_words": sum(self.user_participation[student_name]),
            "discussion_text_id": self.discussion_text.text_id,
        }
        return ret

    def get_curr_proficiency_sub_types(self):
        """
        Returns the sub type(s) of the currently
        selected discussion text.
        """
        return self.discussion_text.get_proficiency_domain()
