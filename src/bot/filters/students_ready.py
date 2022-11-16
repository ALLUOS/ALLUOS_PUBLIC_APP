from telegram import Message
from telegram.ext import BaseFilter

from ..util import get_group_chat_id_from_message
from ...backend.room_manager_storage import get_room_manager_of_group

class StudentsAreReadyFilter(BaseFilter):
    """
    Checks whether enough students are ready to start a task.
    """


    def __init__(self, num_of_students: int):
        """
        Initializes the filter.

        Args:
            num_of_students (int): The number of students needed to start the task.
        """
        self._num_of_students = num_of_students


    def filter(self, message: Message):
        """
        Checks whether enough students are ready to start a task.
        """
        room_manager = get_room_manager_of_group(get_group_chat_id_from_message(message))
        return (len(room_manager.get_joined_student_list()) >= self._num_of_students) and room_manager.can_execution_start()
