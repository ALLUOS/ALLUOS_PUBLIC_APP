import time
import logging
from typing import List
from .db.group import get_students_in_group
from .db.task import get_min_number_of_participants, get_playable_tasks_for_number_of_participants
from .entities.student import Student

logger = logging.getLogger(__name__)


class RoomManager:
    """
    Manages the transition and instanciation of the different tasks for a single group.
    """

    def __init__(self, group_chat_id: str):
        """
        Initializes the room manager for a given group.

        Args:
            group_chat_id (str): The id of the group chat from telegram.
        """
        self._group_chat_id: str = group_chat_id
        self._full_student_list: list = get_students_in_group(
            self._group_chat_id)
        self._joined_student_dict: dict = {}

        # define some more fields that can be used to decide whether the execution can be started or not
        self._min_number_of_students: int = get_min_number_of_participants()
        self._running_task = False
        self._task_selection_shown = False

        # Tracker for restart responses
        self._restart_counter = {
            "yes": 0,
            "no": 0
        }
        self._restart_users_responded = []

        # Selected user for task selection or codeword entering
        self.selected_user = None

        # Fields for tracking group progress through storyline
        self._current_task_count = 0
        self._current_task = None

        # Current passcode as a string
        self._passcode = '1234'

        # List of all task names, empty for now and filled after group has joined
        self._available_tasks = []

        # List number of repetitions of each task
        self._reps_counter = {
            "sentence correction": 0,
            "vocabulary guessing": 0,
            "discussion": 0
        }

    def set_available_tasks(self):
        """
        Sets the list of playable tasks based on the number of joined students
        """

        number_of_players = len(self._joined_student_dict)
        task_names = get_playable_tasks_for_number_of_participants(
            number_of_players)
        self._available_tasks = task_names

    def reset_restart_poll(self):
        """
        Resets the counter of the chosen answers regarding restarting the journey as well as the list keeping tracking of which user has already responded
        """
        self._restart_counter = {
            "yes": 0,
            "no": 0
        }
        self._restart_users_responded = []

    def update_restart_poll(self, is_yes, user_telegram_id):
        """
        Updates the dictionary tracking the responses
        """
        # Check if the user has already responded
        if not user_telegram_id in self._restart_users_responded:
            # Check if the user is active user
            if user_telegram_id in self.get_joined_student_telegram_ids():
                # Add user to list of users that have already responded
                self._restart_users_responded.append(user_telegram_id)
                if is_yes:
                    # Update "yes" counter
                    self._restart_counter["yes"] += 1
                else:
                    # Update "no" counter
                    self._restart_counter["no"] += 1

    def get_poll_restart_result(self) -> bool:
        """
        Evaluates the poll results and returns a boolean if the application should restart (no restart in case of tie)
        """
        return self._restart_counter["yes"] > self._restart_counter["no"]

    def all_users_responded_to_poll(self) -> bool:
        """
        Checks if all (active) users have responded to the poll count
        """
        # Count total responses
        response_count = self._restart_counter["yes"] + self._restart_counter["no"]
        return response_count >= self.get_number_of_joined_students()

    def get_available_tasks(self):
        """
        Returns a list of the tasks that may be chosen by the group
        """
        return self._available_tasks

    def set_passcode(self, passcode):
        """
        Sets the current passcode for the group
        """
        self._passcode = passcode

    def get_passcode(self) -> str:
        """
        Gets the current passcode for the group
        """
        return self._passcode

    def set_selected_user(self, user):
        """
        Sets the user selected for choosing a task
        """
        self.selected_user = user

    def get_selected_user(self):
        """
        Gets the user selected for choosing a task
        """
        return self.selected_user

    def reset_current_task_count(self):
        """
        Returns the task counter
        """
        self._current_task_count = 0

    def get_current_task_count(self) -> int:
        """
        Returns the current task counter of the group
        """
        return self._current_task_count

    def get_current_task(self) -> str:
        """
        Returns the current task name of the group
        """
        return self._current_task

    def next_task(self, task_name):
        """
        Sets the current task of the group
        """
        # Increment the current task count
        self._current_task_count += 1
        # Set the name of the current task
        self._current_task = task_name
        # Remove that task from list of eligible tasks for next task
        self._available_tasks.remove(task_name)

    def current_is_discussion_task(self) -> bool:
        """
        Returns whether the current group task is the discussion task
        """
        return self._current_task == 'discussion'

    def get_full_student_list(self) -> List[Student]:
        """
        Returns the list of students that are present in the group.
        """
        return self._full_student_list

    def add_student_to_joined_list(self, telegram_username: str) -> bool:
        """
        Adds a student to the list of joined students.

        Args:
            telegram_user_name (str): The telegram username of the student to add.

        Returns:
            A boolean indicating whether the student was added or not.
        """
        was_student_added = False

        if not self.is_joined_student(telegram_username):
            # Search the student that should be added
            student_to_add = None
            for student in self._full_student_list:
                if student.get_telegram_id() == telegram_username:
                    student_to_add = student
            # add the student
            if student_to_add:
                self._joined_student_dict[telegram_username] = student_to_add
                was_student_added = True
                logger.info(
                    'Student {} was added to list of joined students.'.format(
                        telegram_username))
            else:
                logger.warning(
                    'Student {} is not in the list of known students ({}) and cannot be added to the list of joined students.'.
                    format(telegram_username, str(self._full_student_list)))
        else:
            logger.info('Student with username {} is already in the list of joined students ({}).'.format(
                telegram_username, self._joined_student_dict))

        return was_student_added

    def did_everyone_join(self) -> bool:
        # checks wether every person confirm their readyness
        return len(self._joined_student_dict) == len(self._full_student_list)

    def get_number_of_joined_students(self) -> int:
        """
        Returns the number of currently joined students.
        """
        return len(self._joined_student_dict)

    def get_joined_student_list(self) -> List[Student]:
        """
        Returns the list of all joined student objects
        (the students that participate in the task).
        """
        print("the students that joined so far are:", self._joined_student_dict)
        return list(self._joined_student_dict.values())

    def get_joined_student_telegram_ids(self):
        """
        Returns the list of all joined students as a list of telegram ids
        """
        return [student.get_telegram_id() for student in list(self._joined_student_dict.values())]

    def reset_joined_students(self):
        """
        Resets the joined students.
        """
        self._joined_student_dict = {}
        self._running_task = False
        self._task_selection_shown = False

    def reset_start_time(self):
        self._joining_phase_start_time = time.time()

    def has_task_started(self):
        """
        Returns true, if there is already a task running.
        """
        return self._running_task

    def is_joined_student(self, telegram_username: str) -> bool:
        """
        Checks whether the given username has already joined.
        """
        return telegram_username in self._joined_student_dict.keys()

    def repeat_current_task(self, task_name):
        """
        Adds task back to list of available task.
        """
        # Decrease task count, as if the task was not completed yet
        self._current_task_count += -1
        # Add that task to list of eligible tasks for next tasks
        self._available_tasks.append(task_name)
        
    def increment_task_rep_count(self, task_name):
        """
        Increment the count of times the task ahs been repeated.
        """    
        self._reps_counter[task_name] += 1

    def reset_reps_counter(self):
        self._reps_counter = {
            "sentence correction": 0,
            "vocabulary guessing": 0,
            "discussion": 0
        }