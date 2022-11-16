from .sentence_correction import SentenceCorrection
from ..db.task import create_sentence_corr_task
from ..db.student_proficiency import update_student_proficiency
from ..db.student_data import update_student_data
from ..room_manager_storage import get_room_manager_of_group

singeltons = {}


def get_sentence_correction_task_of_group(group_chat_id: str) -> SentenceCorrection:
    """
    Returns the SentenceCorrection of the group.

    Args:
        group_chat_id (str): The id of the group chat from telegram.

    Returns:
        The SentenceCorrection instance that is used by the group.
    """
    group_singelton = singeltons.get(group_chat_id)

    if not group_singelton:

        active_users = get_room_manager_of_group(group_chat_id).get_joined_student_list()
        sentence_correction_task = create_sentence_corr_task(active_users)
        group_singelton = sentence_correction_task
        singeltons[group_chat_id] = group_singelton

    return group_singelton


def remove_sentence_correction_task_of_group(group_chat_id: str):
    """
    Removes the SentenceCorrection of the group from the list of singeltons.

    Args:
        group_chat_id (str): The id of the group chat from telegram.
    """
    # Save data to the database
    for student in get_room_manager_of_group(group_chat_id).get_joined_student_list():
        update_student_proficiency(student)
        update_student_data(student)
    # Remove singleton
    singeltons.pop(group_chat_id, None)
