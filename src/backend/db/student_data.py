from .connection import get_connection, close_connection
from ..adaptability.proficiency import Proficiency, Grammar, Vocabulary
import psycopg2
from psycopg2.extras import execute_values
import logging

logger = logging.getLogger(__name__)

def insert_student_data(student):
    # Get the student data as a list with the student id
    data = student.get_data_as_list()
    # Upload results to database table 
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur = conn.cursor()
        insert_query = 'INSERT INTO student_data (student_id, data_field, value) VALUES %s'
        execute_values(cur, insert_query, data)    
        conn.commit()    
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)
    
def delete_student_data(student):
    # Get the students ID
    student_id = student.get_id()
    # Delete from table
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """DELETE FROM student_data WHERE student_id = '%s';"""
        cur.execute(query, (student_id, ))
        conn.commit()   
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)    

def update_student_data(student):
    # First, delete all rows from student data table for the current user
    delete_student_data(student)
    # Then insert the data
    insert_student_data(student)

def get_student_data(student_id):
    """
    Returns a proficiency object that is initialized with the values from the database
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """SELECT data_field, value FROM student_data WHERE student_id = '%s'"""
        cur.execute(query, (student_id, ))
        records = cur.fetchall()
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)
    # Parse rows into dictionary
    return rows_to_data(records)

def rows_to_data(rows) -> {}:
    """ 
    Parses rows from database into a dictionary
    """
    # Initialize empty dictionary
    data = {}
    # Go through rows
    for row in rows:
        # Get proficiency_id and value
        data_field = row[0]
        value = row[1]
        data[data_field] = value
    # Return dictionary
    return data


