import psycopg2
from psycopg2 import sql
import logging
from .connection import get_connection, close_connection
from ..entities.discussion_text import DiscussionText

logger = logging.getLogger(__name__)


def get_random_discussion_text() -> DiscussionText:
    '''
    Get a random discussion text.

    Parameters
    ---------
        group_id : int
            Unique group identifier.

    Returns
    ---------
        discussion_text : DiscussionText
            Discussion text object containing
            all text metadata and questions.
    '''
    ret = ()
    query = """
        SELECT *
        FROM discussion_data
        ORDER BY RANDOM()
        LIMIT 1;
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = sql.SQL(query)
        cur.execute(query)
        ret = cur.fetchone()

    except psycopg2.Error as e:
        logger.error(e)

    finally:
        cur.close()
        close_connection(conn)

    assert len(ret) > 0, (
            'A random discussion '
            'text could not be '
            'retrieved from the db.'
        )

    return DiscussionText(*ret)

def get_random_discussion_text_based_on(subtype, difficulty) -> DiscussionText:
    '''
    Filter the database for a subtype and a difficulty before retrieving a random discussion text.

    Returns
    ---------
        discussion_text : DiscussionText
            Discussion text object containing
            all text metadata and questions.
    '''
    ret = ()
    query = """
        SELECT *
        FROM discussion_data
        WHERE proficiency_domain = %s AND difficulty = %s
        ORDER BY RANDOM()
        LIMIT 1;
    """.format
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = sql.SQL(query)
        cur.execute(query, (subtype,difficulty))
        ret = cur.fetchone()

    except psycopg2.Error as e:
        logger.error(e)

    finally:
        cur.close()
        close_connection(conn)

    assert len(ret) > 0, (
            'A random discussion '
            'text could not be '
            'retrieved from the db.'
        )

    return DiscussionText(*ret)
