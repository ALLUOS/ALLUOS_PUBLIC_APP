from abc import ABC, abstractmethod
from ..tools import random_list_index
from .base_task import Task
import numpy as np
import logging
import datetime

logger = logging.getLogger(__name__)

# Allow the group to fail two rounds before considering the task unsuccessful
ALLOWED_FAILS = 2

class SequentialTask(Task):

    def __init__(self, users, difficulty, group_iterations):
        # Stores information about all users currently working on the task
        self.all_users = users
        # Stores information about the users that have not yet had their turn
        self.remaining_users = users.copy()
        # Stores the user that is currently selected (empty at first)
        self.selected_user = None
        # Check if this is the first iteration of the task
        self.is_first_iteration = True
        # Set difficulty of the task
        self.difficulty = difficulty
        # Set number of total iterations
        self.code_length = group_iterations
        # Set current iteration and counter for correct iterations
        self.curr_group_iterations = 0
        self.curr_group_correct_iterations = 0
        self.curr_group_incorrect_iterations = 0
        # Set number of correct responses per iteration
        self.curr_correct = 0
        # Get random code of length of group iterations
        self.code = np.random.randint(0, 10, self.code_length)
        # Stores previous iteration start for adaptive data.
        self.previous_iteration_start = datetime.datetime.now()
        # Stores previous iteration duration for adaptive data.
        self.previous_iteration_duration = 0
        # Counter for messages sent by selected user.
        self.n_messages_selected_user = 0
        # Counter for messages sent by non-selected users.
        self.n_messages_non_selected_users = 0

    @abstractmethod
    def get_task_instructions(self):
        pass

    @abstractmethod
    def get_curr_proficiency_sub_types(self):
        pass

    def get_task_variation(self):
        pass

    def is_finished(self):
        """
        Checks if the task has been fully completed
        """
        return self.curr_group_correct_iterations == self.code_length or self.curr_group_incorrect_iterations > ALLOWED_FAILS

    def is_success(self):
        """
        Checks if the task has been successful
        """
        return self.curr_group_incorrect_iterations <= ALLOWED_FAILS

    def select_next_user(self):
        """
        Internally selects the next user that should answer the next sentence. Does not return anything
        """
        # Choose random index for the selected user
        idx = random_list_index(self.remaining_users)
        # Select this user
        self.selected_user = self.remaining_users[idx]
        # Remove from list of remaining users
        self.remaining_users.pop(idx)

    def get_selected_user(self):
        """
        Return telegram id of currently selected user
        """
        return self.selected_user.get_telegram_id()

    def is_group_iteration_finished(self):
        """
        Checks if all users have been given one sentence and returns a boolean
        """
        return len(self.remaining_users) == 0

    def is_correct_group_iteration(self):
        """
        Checks if all answers in this iteration have been correct and returns a boolean
        """
        return self.curr_correct >= len(
            self.all_users)  # TODO: Decide if self.curr_correct >= len(self.all_users)-1 is the better one

    def reset_attributes_for_next_individual_iteration(self):
        """
        Resets adaptive data attributes at the end
        of an individual iteration.
        """
        now = datetime.datetime.now()
        self.previous_iteration_duration = now - \
            self.previous_iteration_start
        self.previous_iteration_start = now
        # Reset message counters.
        self.n_messages_selected_user = 0
        self.n_messages_non_selected_users = 0

    def next_group_iteration(self):
        """
        Starts the next group iteration, resets all associated variables and increments counters
        """
        # Update previous iteration duration and start
        # time for adaptive data.
        now = datetime.datetime.now()
        self.previous_iteration_duration = now - \
            self.previous_iteration_start
        self.previous_iteration_start = now
        # Reset message counters.
        self.n_messages_selected_user = 0
        self.n_messages_non_selected_users = 0
        # TODO: Adjust difficulty here

        self.curr_group_iterations += 1

        self.curr_correct = 0
        self.remaining_users = self.all_users.copy()

    def increment_correct_group_iteration(self):
        """
        Increments counter of correct group iterations
        """
        self.curr_group_correct_iterations += 1
        # Also, update the student data field of codeword pieces collected
        self.increment_data_for_all_users(
            field='codeword_pieces_collected', increment=1)

    def increment_incorrect_group_iteration(self):
        """
        Increments counter of incorrect group iterations
        """
        self.curr_group_incorrect_iterations += 1

    def increment_correct_count(self):
        """
        Increments the counter of correct responses in current group iteration
        """
        self.curr_correct += 1

    def check_codeword(self, msg):
        """
        Returns a boolean indicating whether or not the codeword is correct
        """
        return "".join(self.code.astype(str)) in msg

    def update_proficiencies(self, correct):
        """
        Updates all user proficiencies based on the response and sub-type(s) the task relates to
        """
        # Get sub-types of current task
        proficiency_sub_types = self.get_curr_proficiency_sub_types()
        # Go through all users
        for user in self.all_users:
            # Check if user is currently selected -> Stronger update
            if user == self.selected_user:
                # Apply strong update
                user.update_proficiency(
                    proficiency_sub_types, correct, group_update=False)
            else:
                # Apply group update
                user.update_proficiency(
                    proficiency_sub_types, correct, group_update=True)

    def log_proficiencies(self):
        """
        Logs the proficiency of all users in this task
        """
        for user in self.all_users:
            logger.info(
                'Test information: Proficiency for user {}: {}'.format(
                    str(user),
                    str(user.get_proficiency())))

    def increment_data_for_all_users(self, field, increment=1):
        """
        Goes through all users and increments the given data field for all of them
        """
        for student in self.all_users:
            student.increment_data(field=field, increment=increment)

    def get_codeword(self) -> str:
        """
        Returns the codeword as a string
        """
        return "".join(self.code.astype(str))
