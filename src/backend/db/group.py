import psycopg2
import logging
import uuid

from typing import List

from .connection import get_connection, close_connection
from .student import get_student
from .student_data import get_student_data
from ..entities.group import Group
from ..entities.student import Student
from ..result import BackendResult
from ...telegram.groups.group_handler import create_telegram_group, add_user_to_channel, add_bot_to_channel, get_chat_invite_link, set_group_logo
from .student_proficiency import get_student_proficiency

logger = logging.getLogger(__name__)
standard_group_name = 'Escape Mission {}'
standard_group_description = r"""Escape the rooms by using english with your crew. Can you make it out in time? Mission code: {}. You can begin your journey by typing "\start" in the group chat."""
max_number_of_group_members = 4


def create_group(telegram_name: str) -> BackendResult:
    """
    Creates a new group and adds the user to it.

    Args:
        telegram_name (str): The telegram name of the user for whom the group is created.

    Returns:
        The result with the registration code as message if creation was successful. Otherwise false.
    """
    result = BackendResult(False)
    cur = None
    conn = None
    try:
        # we use an UUID for the invitation code
        invitation_code = uuid.uuid4()

        # first, create the group in telegram and get the invitation link for the group
        group = create_telegram_group(
            standard_group_name.format(str(invitation_code)[: 13]),
            standard_group_description.format(invitation_code))
        invitation_url = get_chat_invite_link(group)
        chat_id = group.id

        # then upload the group logo to the newly created group
        set_group_logo(chat_id)

        # create the database entry
        conn = get_connection()
        cur = conn.cursor()
        insert_group_statement = 'INSERT INTO telegram_group(chat_id, invitation_url, invitation_code) VALUES (%s, %s, %s) RETURNING id'
        cur.execute(insert_group_statement,
                    (chat_id, invitation_url, invitation_code))
        group_id = cur.fetchone()[0]

        # add the bot and user to the group in telegram
        add_bot_to_channel(chat_id)
        add_user_to_channel(chat_id, telegram_name)

        # create the connection between user and group in the database
        student = get_student(telegram_name)
        if student is None:
            logger.warning('Student cannot be found.')
            conn.rollback()
        else:
            insert_student_group_statement = 'INSERT INTO student_group (student_id, group_id) VALUES (%s, %s)'
            cur.execute(insert_student_group_statement, (student.id, group_id))
            conn.commit()
            result = BackendResult(True, invitation_code)
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)

    return result


def _find_group_with_registration_code(registration_code: str) -> Group:
    """
    Seaches the group that has registration code.

    Args:
        registration_code (str): The regirstration code of the group.

    Returns:
        The group if it exists, otherwise None.
    """
    group_or_none = None
    select_statement = 'SELECT id, chat_id, invitation_url, invitation_code FROM telegram_group WHERE invitation_code = %s LIMIT 1'
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(select_statement, (registration_code, ))
        result = cur.fetchone()
        if result is not None:
            group_or_none = Group(result[0], result[1], result[2], result[3])
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)
    return group_or_none


def _can_add_student_to_group(group_id: int) -> bool:
    """
    Checks whether another student can be added to the group.

    Args:
        group_id (int): The id of the group that has to be checked.

    Returns:
        True if another student can be added to the group. Otherwise false is returned.
    """
    can_be_added = False
    select_statement = 'SELECT COUNT(student_id) FROM student_group WHERE group_id = %s GROUP BY group_id'
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(select_statement, (group_id, ))
        number_of_members = cur.fetchone()[0]
        can_be_added = number_of_members < max_number_of_group_members
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)
    return can_be_added


def add_student_to_group(
        registration_code: str, telegram_name: str) -> BackendResult:
    """
    Adds the given student to the group with the registration code.

    Args:
        registration_code (str): The registration to find the group with.
        telegram_name (str): The telegram name of the student that should be added.

    Returns:
        An instance of the BackendResult class holding a indicator whether the request was successful or not and an optional message.
    """
    group = _find_group_with_registration_code(registration_code)
    result = BackendResult(False, 'An error occured')
    if group is None:
        result = BackendResult(
            False,
            'I was not able to find the group with the registration code {}. Is it correct?'.
            format(registration_code))
    else:
        if not _can_add_student_to_group(group.get_id()):
            result = BackendResult(False, 'The group is already full.')
        else:
            student = get_student(telegram_name)
            if student is None:
                result = BackendResult(False, 'I cannot add you to the group.')
            else:
                successful = True
                try:
                    # create the database entry
                    conn = get_connection()
                    cur = conn.cursor()
                    insert_student_group_statement = 'INSERT INTO student_group (student_id, group_id) VALUES (%s, %s)'
                    cur.execute(insert_student_group_statement,
                                (student.id, group.id))
                    conn.commit()
                except psycopg2.Error as e:
                    logger.error(e)
                    successful = False
                    result = BackendResult(
                        False, 'I cannot add you to the group.')
                finally:
                    if cur:
                        cur.close()
                    close_connection(conn)
                if successful:
                    result = result = BackendResult(
                        True, group.get_invitation_url())
    return result


def get_students_in_group(group_id: str) -> List[Student]:
    """
    Retrieves all students that are in the group.

    Args:
        group_id (str): The id of the telegram group channel.

    Returns:
        A list of students that are in the group.
    """
    student_list = []
    try:
        query = """
        SELECT student.id, student.telegram_name, student.name FROM student
            INNER JOIN student_group
                ON (student.id = student_group.student_id)
            INNER JOIN telegram_group
                ON (telegram_group.id = student_group.group_id)
            WHERE telegram_group.chat_id = %s
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, (group_id, ))
        records = cur.fetchall()
        for student_record in records:
            # Store student id
            student_id = student_record[0]
            # Load proficiency for student
            proficiency = get_student_proficiency(student_id)
            # Load student data from database
            data = get_student_data(student_id)
            # Create student object and append to list
            student_list.append(
                Student(
                    id=student_id, telegram_id=student_record[1],
                    name=student_record[2],
                    proficiency=proficiency, data=data))
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)

    return student_list
