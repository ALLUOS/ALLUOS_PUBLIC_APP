from .connection import get_connection, close_connection
from ..entities.student import Student
from ..adaptability.proficiency import Proficiency, Grammar, Vocabulary, Others
import psycopg2
from psycopg2.extras import execute_values
import logging

logger = logging.getLogger(__name__)

def insert_student_proficiency(student):
    # Get the proficiency as a list
    proficiency_list = student.get_proficiency_as_list()
    # Upload results to database table 
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur = conn.cursor()
        insert_query = 'INSERT INTO student_proficiency (student_id, proficiency_id, value) VALUES %s'
        execute_values(cur, insert_query, proficiency_list)    
        conn.commit()    
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)
    
def delete_student_proficiency(student):
    # Get the students ID
    student_id = student.get_id()
    # Delete from table
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """DELETE FROM student_proficiency WHERE student_id = '%s';"""
        cur.execute(query, (student_id, ))
        conn.commit()   
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)    

def update_student_proficiency(student):
    # First, delete all rows from student proficiency table for the current user
    delete_student_proficiency(student)
    # Then insert the proficiency
    insert_student_proficiency(student)

def get_student_proficiency(student_id):
    """
    Returns a proficiency object that is initialized with the values from the database
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """SELECT proficiency_id, value FROM student_proficiency WHERE student_id = '%s'"""
        cur.execute(query, (student_id, ))
        records = cur.fetchall()
    except psycopg2.Error as e:
        logger.error(e)
    finally:
        if cur:
            cur.close()
        close_connection(conn)
    # Parse rows into proficiency object
    return rows_to_proficiency(records)

def rows_to_proficiency(rows) -> Proficiency:
    """ 
    Parses rows from database into Proficiency object
    """
    # Initialize empty dictionaries
    grammar_dict = {}
    vocab_dict = {}
    other_dict = {}
    # Go through rows
    for row in rows:
        # Get proficiency_id and value
        proficiency_id = row[0]
        value = row[1]
        # Check if sub_type domain is Grammar or Vocab and add entry to corresponding dictionary
        if proficiency_id < 20:
            grammar_dict[Grammar(proficiency_id)] = value
        elif proficiency_id < 100:
            vocab_dict[Vocabulary(proficiency_id)] = value
        else: 
            other_dict[Others(proficiency_id)] = value
    # Return proficiency object based on those two dictionaries
    return Proficiency(initial = False, grammar_dict = grammar_dict, vocab_dict = vocab_dict, others_dict = other_dict)


