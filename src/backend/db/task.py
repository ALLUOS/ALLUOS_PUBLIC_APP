import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import logging
from typing import List

from .connection import get_connection, close_connection
from .task_definition import TASK_DEF_DF, TASK_DEBUG_DEF_DF, Task_cols
from ..entities.task import Task
from src.backend.tasks.vocabulary_description import VocabularyDescription
from src.backend.tasks.sentence_correction import SentenceCorrection
from src.backend.tasks.discussion import Discussion
# from src.backend.tasks.listening import Listening
from src.backend.entities.student import Student
from src.misc.constants import LISTENING_TASK_NAME, SEN_CORR_TASK_NAME, VOC_DESC_TASK_NAME
from src.misc.debug_mode import is_debug_mode_active


logger = logging.getLogger(__name__)

def get_min_number_of_participants() -> int:
    """
    Looks at the minimum amount of players for each tasks.
    Returns the smallest number.

    Returns:
        The minimum participant number.
    """

    if is_debug_mode_active():
        min_participants = TASK_DEBUG_DEF_DF[Task_cols.MIN_NUM_OF_PLAYERS].min()
    else:
        min_participants = TASK_DEF_DF[Task_cols.MIN_NUM_OF_PLAYERS].min()

    return min_participants


def get_playable_tasks_for_number_of_participants(
        num_of_participants: int) -> List[str]:
    """
    Returns a list of the names of all tasks that can be started with the number of participants.

    Args:
        num_of_participants (int): The number of participants the task should be playable with.

    Returns:
        A list of all task names that are playable.
    """

    if is_debug_mode_active():
        tasks_df = TASK_DEBUG_DEF_DF[TASK_DEBUG_DEF_DF[Task_cols.MIN_NUM_OF_PLAYERS]
                                     <= num_of_participants]
    else:
        tasks_df = TASK_DEF_DF[TASK_DEF_DF[Task_cols.MIN_NUM_OF_PLAYERS] <=
                               num_of_participants]

    task_names = tasks_df[Task_cols.NAME].tolist()
    lower_case_task_names = [task_name.lower() for task_name in task_names]

    return lower_case_task_names


def create_sentence_corr_task(active_users: List[Student]) -> SentenceCorrection:

    if is_debug_mode_active():
        sen_cor_df = get_task_debug_df_row_by_name(SEN_CORR_TASK_NAME)
    else:
        sen_cor_df = get_task_df_row_by_name(SEN_CORR_TASK_NAME)

    id, name, min_num_players, num_iterations = sen_cor_df.values.tolist()[0]
    temp_task = Task(id, name, min_num_players, num_iterations)

    return SentenceCorrection(
        users=active_users, difficulty=3,
        group_iterations=temp_task.get_num_of_iterations())


def create_vocab_description_task(active_users: List[Student]) -> VocabularyDescription:

    if is_debug_mode_active():
        voc_desc_df = get_task_debug_df_row_by_name(VOC_DESC_TASK_NAME)
    else:
        voc_desc_df = get_task_df_row_by_name(VOC_DESC_TASK_NAME)

    id, name, min_num_players, num_iterations = voc_desc_df.values.tolist()[0]
    temp_task = Task(id, name, min_num_players, num_iterations)

    return VocabularyDescription(
        users=active_users, difficulty=3,
        group_iterations=temp_task.get_num_of_iterations())


def create_discussion_task(active_users: List[Student]) -> Discussion:

    if is_debug_mode_active():
        return Discussion(users=active_users, difficulty=3, timelimit=35)
    else:
        return Discussion(users=active_users, difficulty=3, timelimit=180)


"""
def create_listening_task(active_users: List[Student]) -> Listening:

    if is_debug_mode_active():
        listening_df = get_task_debug_df_row_by_name(LISTENING_TASK_NAME)
    else:
        listening_df = get_task_df_row_by_name(LISTENING_TASK_NAME)

    id, name, min_num_players, num_iterations = listening_df.values.tolist()[0]

    return Listening(
        users=active_users, difficulty=3,
        group_iterations=num_iterations)
"""

def get_task_df_row_by_name(task_name):
    return TASK_DEF_DF.loc[TASK_DEF_DF[Task_cols.NAME] == task_name]


def get_task_debug_df_row_by_name(task_name):
    return TASK_DEBUG_DEF_DF.loc[TASK_DEBUG_DEF_DF[Task_cols.NAME] == task_name]


def insert_sentence_correction_adaptive_data_entry(entry: dict) -> None:
    """
    Inserts a new sentence correction task iteration
    entry into the relevant adaptive data table.
    """
    timedelta = str(entry['turn_duration']).split(':')
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = sql.SQL("""
            INSERT INTO sentence_correction_adaptive_data (
                student_id,
                group_id,
                turn_start,
                turn_duration,
                performance,
                messages_elected_user,
                messages_other_users,
                sentence_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """)
        cur.execute(
            query,
            (str(entry['student_id']),
             entry['group_id'],
             entry['turn_start'].strftime("%Y-%m-%d %H:%M:%S"),
             f"{int(timedelta[1])} minutes {round(float(timedelta[2]))} seconds",
             str(entry['performance']),
             str(entry['messages_elected_user']),
             str(entry['messages_other_users']),
             str(entry['sentence_id']),))
        conn.commit()
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)


def insert_vocabulary_guessing_adaptive_data_entry(entry: dict) -> None:
    """
    Inserts a new vocabulary guesing task iteration
    entry into the relevant adaptive data table.
    """
    timedelta = str(entry['turn_duration']).split(':')
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = sql.SQL("""
            INSERT INTO vocabulary_guessing_adaptive_data (
                student_id,
                group_id,
                turn_start,
                turn_duration,
                correct,
                skipped,
                messages_elected_user,
                messages_other_users,
                description_texts,
                vocab_word)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """)
        cur.execute(
            query,
            (str(entry['student_id']),
             entry['group_id'],
             entry['turn_start'].strftime("%Y-%m-%d %H:%M:%S"),
             f"{int(timedelta[1])} minutes {round(float(timedelta[2]))} seconds",
             str(entry['correct']),
             str(entry['skipped']),
             str(entry['messages_elected_user']),
             str(entry['messages_other_users']),
             str(entry['description_texts']),
             str(entry['vocab_word']),))
        conn.commit()
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)


def insert_discussion_adaptive_data_entry(entry: dict) -> None:
    """
    Inserts a new discussion task iteration
    entry for a single user into the relevant adaptive data table.
    """

    """
    this function is commented out, because the creation of the `discussion_adaptive_data` table
    is not implemented, yet.
    """

    '''
    timedelta = str(entry['discussion_duration']).split(':')
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = sql.SQL("""
            INSERT INTO discussion_adaptive_data (
                student_id,
                group_id,
                discussion_start,
                discussion_duration,
                topic_easy_to_understand,
                learned_something,
                group_performance_rating,
                n_discussion_words,
                discussion_text_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """)
        cur.execute(query,
                (
                    str(entry['student_id']),
                    entry['group_id'],
                    entry['discussion_start'].strftime("%Y-%m-%d %H:%M:%S"),
                    f"{int(timedelta[1])} minutes {round(float(timedelta[2]))} seconds",
                    str(entry['topic_easy_to_understand']),
                    str(entry['learned_something']),
                    str(entry['group_performance_rating']),
                    str(entry['n_discussion_words']),
                    str(entry['discussion_text_id']),
                )
            )
        conn.commit()
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)
    '''
