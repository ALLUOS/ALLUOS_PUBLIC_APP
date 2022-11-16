import psycopg2
import logging
import datetime

from .connection import get_connection, close_connection
from ..entities.student import Student
from .student_proficiency import get_student_proficiency, insert_student_proficiency
from .student_data import get_student_data, insert_student_data
from ...misc.date_tools import date_to_int
from ..adaptability.proficiency import Grammar, Vocabulary
from ...misc.constants import (SEN_CORR_TASK_NAME, DISCUSSION_TASK_NAME, VOC_DESC_TASK_NAME)

logger = logging.getLogger(__name__)


def get_student(telegram_name: str) -> Student:
    """
    Gets the student with the specified telegram name from the database.

    Args:
        telegram_name (str): The name from telegram to search the student with.

    Returns:
        A student object if the student was found. Otherwise, None is returned.
    """
    student_or_none = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = 'SELECT id, telegram_name, name FROM student WHERE telegram_name = %s'
        cur.execute(query, (telegram_name, ))
        student_record = cur.fetchone()
        if student_record is not None:
            # Store student id
            student_id = student_record[0]
            # Load proficiency for student
            proficiency = get_student_proficiency(student_id)
            # Load student data from database
            data = get_student_data(student_id)
            # Create student object
            student_or_none = Student(id=student_id, telegram_id=student_record[1], name=student_record[2], proficiency=proficiency, data=data)
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)
    return student_or_none


def create_student(telegram_name: str, name: str) -> Student:
    """
    Creates a new student with the given values in the database.

    Args:
        telegram_name (str): The name from telegram
        name (str): The name of the student.

    Returns:
        The new created student entity.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        insert_statement = 'INSERT INTO student(telegram_name, name) VALUES (%s, %s) RETURNING id'
        cur.execute(insert_statement, (telegram_name, name))
        student_id = cur.fetchone()[0]
        conn.commit()
        # Create student object with the id and save inital date of last played
        student = Student(student_id, telegram_name, name,
                          data={'last_played': date_to_int(datetime.date.today()), 'consecutive_days': 1,
                                'highest_streak': 1})
        # Also create empty proficiencies for the student in the database
        insert_student_proficiency(student)
        # Also create default values for 'last_played' and 'consecutive_days' fields in the database
        insert_student_data(student)
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)
    return student


def get_n_recent_adaptive_data_entries(
    student_id:str,
    task_name:str,
    n:int=5
) -> list:
    """
    Retrieves the n most-recent
    adaptive data entries for the
    requested student relevant to the
    requested task.

    Parameters
    ---------
        student_id : str
            Student id from database.
        task_name : str
            Name of task.
        n : int
            Number of most-recent
            entries to return.
    """
    records = []
    try:
        conn = get_connection()
        cur = conn.cursor()
        if task_name == SEN_CORR_TASK_NAME.lower():
            query = """
                SELECT turn_duration, sentence_sub_type
                FROM sentence_correction_adaptive_data
                WHERE student_id = %s
                ORDER BY turn_start DESC
                LIMIT %s;
            """
        elif task_name == VOC_DESC_TASK_NAME.lower():
            query = """
                SELECT turn_duration, vocab_sub_type
                FROM vocabulary_guessing_adaptive_data
                WHERE student_id = %s
                ORDER BY turn_start DESC
                LIMIT %s;
            """
        elif task_name == DISCUSSION_TASK_NAME.lower():
            query = """
                SELECT discussion_duration, topic_easy_to_understand, learned_something, group_performance_rating, n_discussion_words
                FROM discussion_adaptive_data
                WHERE student_id = %s
                ORDER BY discussion_start DESC
                LIMIT %s;
            """
        cur.execute(query, (student_id, n))
        records = cur.fetchall()
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)

    return records
