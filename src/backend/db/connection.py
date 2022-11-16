import psycopg2
import logging
import pandas as pd

db_config = {}
db_config_without_options = {}
logger = logging.getLogger(__name__)                                   


def set_db_config(new_db_config: dict):
    """
    Sets the database configuration to use.

    Args:
        new_db_config (dict): A dictionary holding the necessary information to enable a database connection.
    """
    global db_config
    logger.info('Set database config: ')
    logger.info(new_db_config)
    for key, item in new_db_config.items():
        db_config[key] = item
    logger.debug('New database config: ')
    logger.debug(db_config)
    _set_db_config_without_options()
    return db_config


def _set_db_config_without_options():
    """
    Creates a database configuration that does not use the options.
    """
    global db_config_without_options
    db_config_without_options = db_config.copy()
    db_config_without_options.pop('options', None)


def get_connection(use_options: bool = True):
    """
    Creates a new connection to the database. 

    Args:
        use_options (bool): If true (default), the database configuration with the options is used.

    Returns:
        A connection to the database.
    """
    try:
        logger.debug('Open a new connection to the database.')
        # Connect to the postgreSQL server
        if use_options:
            conn = psycopg2.connect(**db_config)
        else:
            conn = psycopg2.connect(**db_config_without_options)
        return conn

    except psycopg2.Error as error:
        logger.error('No new connection was opened: {}'.format(error))
        logger.error(error.pgcode)
        logger.error(error.pgerror)
        # TODO: Exception handling


def close_connection(conn):
    """
    Closes the given connection.

    Args:
        connection: The connection to close.
    """
    try:
        # Closes the connection to the postgreSQL server
        if (conn):
            conn.close()

    except psycopg2.Error as error:
        logger.error(error.pgcode)
        logger.error(error.pgerror)
        # TODO: Exception handling


def read_query_into_df(query, params = None):
    # Open a connection
    conn = get_connection()
    # Try to execute the query
    try:
        return pd.read_sql(query, conn, params = params)
    except psycopg2.Error as error:
        logger.error('Error while reading query {} into dataframe: {}'.format(query, error))
        logger.error(error.pgcode)
        logger.error(error.pgerror)
    # In the end, close the connection 
    close_connection(conn)