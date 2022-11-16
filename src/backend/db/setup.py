import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import sql
import logging
import sys
import pandas as pd

from .connection import get_connection, close_connection

logger = logging.getLogger("db.setup")

def delete_schema(schema: str):
    """
    Deletes the database schema.

    Args:
        schema (str): The database schema to be deleted.
    """
    logger.info('Delete the schema {}'.format(schema))
    try:
        conn = get_connection(use_options=False)
        cur = conn.cursor()
        cur.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE'.format(schema)))
        conn.commit()
    except psycopg2.Error as e:
        logger.exception(e)
        sys.exit()
    finally:
        if cur:
            cur.close()
        close_connection(conn)


def create_schema_and_tables(schema: str):
    """
    Creates all tables.

    Args:
        schema (str): The database schema to be created.
    """
    _create_schema(schema)

    # open a connection to use it for all create statements
    try:
        conn = get_connection(use_options=False)

        # create all tables
        _create_student_table(conn, schema)
        _create_group_table(conn, schema)
        _create_student_group_table(conn, schema)
        _create_student_data_table(conn, schema)
        _create_sentence_correction_data(conn, schema)
        _create_vocab_guessing_table(conn, schema)
        _create_proficiency_table(conn, schema)
        _create_discussion_table(conn, schema)
        _create_student_proficiency_table(conn, schema)
        _create_sentence_correction_adaptive_data_table(conn, schema)
        _create_vocabulary_guessing_adaptive_data_table(conn, schema)
        _create_discussion_adaptive_data_table(conn, schema)
        _create_sentence_correction_adaptive_data_trigger(conn, schema)
        _create_vocabulary_guessing_adaptive_data_trigger(conn, schema)

        conn.commit()
    except psycopg2.Error as e:
        logger.exception(e)
        sys.exit()
    finally:
        close_connection(conn)


def insert_base_data(data_file_locations: dict):
    """
    Inserts all data that is necessary for the bot to run.
    """
    try:
        conn = get_connection()

        # insert all data needed
        _insert_sentence_correction_data(conn, data_file_locations['sentence_correction_task'])
        _insert_vocab_guessing_data(conn, data_file_locations['vocabulary_guessing_task'])
        _insert_proficiency_data(conn, data_file_locations['proficiency_info'])
        _insert_discussion_data(conn, data_file_locations['discussion_task'])

        conn.commit()
    except psycopg2.Error as e:
        logger.exception(e)
        sys.exit()
    finally:
        close_connection(conn)


def create_or_update_tables():
    """
    Ensures that all tables are present in the database.
    If they do not already exist, they are created.
    If they exist, they are updated to match the current database schema.
    """
    # TODO: create or update tables, we need this later for updating a running version


def _create_schema(schema: str):
    """
    Creates the schema.

    Args:
        schema (str): The name of the schema to create.
    """
    # open a connection and get a cursor
    conn = get_connection(use_options=False)
    cur = conn.cursor()
    # drop the schema
    cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}".format(schema)))
    # close everything
    cur.close()
    conn.commit()
    close_connection(conn)

def _create_student_table(conn, schema: str):
    """
    Creates the student table in the database.

    Args:
        conn (connection): The connection that is used to create the table.
        schema (str): The schema in which the table should be created.
    """
    logger.info('Create the student table.')
    create_table_sql = sql.SQL("""
    CREATE TABLE {}.student (
        id SERIAL PRIMARY KEY,
        telegram_name VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(50) NOT NULL
    )
    """).format(sql.Identifier(schema))
    # create the student table
    cur = conn.cursor()
    cur.execute(create_table_sql)
    cur.close()
    logger.info('Created the student table.')

def _create_student_data_table(conn, schema: str):
    """
    Creates the student data table in the database.

    Args:
        conn (connection): The connection that is used to create the table.
        schema (str): The schema in which the table should be created.
    """
    logger.info('Create the student data table.')
    create_table_sql = sql.SQL("""
    CREATE TABLE {}.student_data (
        student_id INTEGER,
        data_field VARCHAR(50) NOT NULL,
        value NUMERIC
    )
    """).format(sql.Identifier(schema))
    # create the student table
    cur = conn.cursor()
    cur.execute(create_table_sql)
    cur.close()
    logger.info('Created the student table.')


def _create_group_table(conn, schema: str):
    """
    Creates the group table.

    Args:
        conn (connection): The connection that is used to create the table.
        schema (str): The schema in which the table should be created.
    """
    logger.info('Create the group table.')
    create_table_sql = sql.SQL("""
    CREATE TABLE {schema}.telegram_group (
        id SERIAL PRIMARY KEY,
        chat_id VARCHAR(50) UNIQUE NOT NULL,
        invitation_url VARCHAR(70) NOT NULL,
        invitation_code VARCHAR(50) UNIQUE NOT NULL
    )
    """).format(schema=sql.Identifier(schema))
    # create the group table
    cur = conn.cursor()
    cur.execute(create_table_sql)
    cur.close()
    logger.info('Created the group table.')


def _create_student_group_table(conn, schema: str):
    """
    Creates the student group table.

    Args:
        conn (connection): The connection that is used to create the table.
        schema (str): The schema in which the table should be created.
    """
    logger.info('Create the student_group table.')
    create_table_sql = sql.SQL("""
    CREATE TABLE {schema}.student_group (
        student_id SERIAL NOT NULL,
        group_id SERIAL NOT NULL,
        PRIMARY KEY (student_id, group_id),
        CONSTRAINT student_group_student_id_fkey FOREIGN KEY (student_id)
            REFERENCES {schema}.student (id) MATCH SIMPLE
            ON UPDATE NO ACTION ON DELETE CASCADE,
        CONSTRAINT student_group_group_id_fkey FOREIGN KEY (group_id)
            REFERENCES {schema}.telegram_group (id) MATCH SIMPLE
            ON UPDATE NO ACTION ON DELETE CASCADE
    )
    """).format(schema=sql.Identifier(schema))
    # create the student_group table
    cur = conn.cursor()
    cur.execute(create_table_sql)
    cur.close()
    logger.info('Created the student_group table.')


def _create_sentence_correction_data(conn, schema):
    """
    Creates the sentence correction data table.

    Args:
        conn (connection): The connection that is used to create the table.
        schema (str): The schema in which the table should be created.
    """
    # TODO: Add FK constraints
    logger.info('Create the sentence_correction_data table.')
    create_table_sql = sql.SQL("""
    CREATE TABLE {schema}.sentence_correction_data (
        id SERIAL PRIMARY KEY,
        sub_type SMALLINT NOT NULL,
        difficulty_level SMALLINT NOT NULL,
        sentence_corpus TEXT NOT NULL,
        correct_answers TEXT ARRAY NOT NULL,
        error_words TEXT ARRAY NOT NULL
    )
    """).format(schema=sql.Identifier(schema))
    # create the sentence_correction_data table
    cur = conn.cursor()
    cur.execute(create_table_sql)
    cur.close()
    logger.info('Created the sentence_correction_data table.')


def _insert_sentence_correction_data(conn, file_location: str):
    """
    Inserts the data for the sentence correction task.
    """
    # read in the csv file and transform it to a list of tuples
    df = pd.read_csv(file_location)
    data = list(df.itertuples(index=False, name=None))
    cur = conn.cursor()
    insert_query = 'INSERT INTO sentence_correction_data (sub_type, difficulty_level, sentence_corpus, correct_answers, error_words) VALUES %s'
    execute_values(cur, insert_query, data, page_size=1000)
    cur.close()


def _create_student_proficiency_table(conn, schema):
    """
    Creates the user proficiency data table.
    Args:
        conn (connection): The connection that is used to create the table.
        schema (str): The schema in which the table should be created.
    """
    logger.info('Create the student proficiency table.')
    create_table_sql = sql.SQL("""
    CREATE TABLE {schema}.student_proficiency (student_id text, proficiency_id smallint, value float
    )
    """).format(schema=sql.Identifier(schema))
    # create the sentence_correction_data table
    cur = conn.cursor()
    cur.execute(create_table_sql)
    cur.close()
    logger.info('Created the student_proficiency table.')


def _create_proficiency_table(conn, schema):
    """
    Creates the proficiency data table.
    Args:
        conn (connection): The connection that is used to create the table.
        schema (str): The schema in which the table should be created.
    """
    logger.info('Create the proficiency_info table.')
    create_table_sql = sql.SQL("""
    CREATE TABLE {schema}.proficiency_info (proficiency_domain text, proficiency_id smallint PRIMARY KEY, proficiency_name text
    )
    """).format(schema=sql.Identifier(schema))
    # create the sentence_correction_data table
    cur = conn.cursor()
    cur.execute(create_table_sql)
    cur.close()
    logger.info('Created the proficiency_info table.')


def _insert_proficiency_data(conn, file_location: str):
    """
    Inserts the data with the proficiency levels.
    """
    df = pd.read_csv(file_location)
    data = list(df.itertuples(index=False, name=None))
    cur = conn.cursor()
    insert_query = 'INSERT INTO proficiency_info (proficiency_domain, proficiency_id, proficiency_name) VALUES %s'
    execute_values(cur, insert_query, data, page_size=1000)
    cur.close()

def _create_vocab_guessing_table(conn, schema):
    """
    Creates the vocab guessing data table.
    Args:
        conn (connection): The connection that is used to create the table.
        schema (str): The schema in which the table should be created.
    """
    # TODO: Add FK constraints
    logger.info('Create the vocabulary guessing data table.')
    create_table_sql = sql.SQL("""
    CREATE TABLE {schema}.vocabulary_guessing_data (id SERIAL PRIMARY KEY, sub_type SMALLINT NOT NULL, word TEXT NOT NULL, difficulty SMALLINT NOT NULL)""").format(schema=sql.Identifier(schema))
    # create the sentence_correction_data table
    cur = conn.cursor()
    cur.execute(create_table_sql)
    cur.close()
    logger.info('Created the vocabulary guessing data table.')

def _insert_vocab_guessing_data(conn, file_location: str):
    """
    Inserts the data for the vocabulary guessing task.
    """
    # read in the csv file and transform it to a list of tuples
    df = pd.read_csv(file_location)
    data = list(df.itertuples(index=False, name=None))
    cur = conn.cursor()
    insert_query = 'INSERT INTO vocabulary_guessing_data (sub_type, word, difficulty) VALUES %s'
    execute_values(cur, insert_query, data, page_size=1000)
    cur.close()

def _create_sentence_correction_adaptive_data_table(
    conn: 'connection',
    schema: str
) -> None:
    """
    Creates the sentence correction adaptive data table.
    """
    logger.info(
            (
                'Creating new sentence correction '
                'adaptive data table.'
            )
        )
    query = sql.SQL("""
        CREATE TABLE {schema}.sentence_correction_adaptive_data
        (
            id SERIAL PRIMARY KEY,
            student_id integer NOT NULL,
            group_id integer NOT NULL,
            turn_start timestamp NOT NULL,
            turn_duration interval NOT NULL,
            performance smallint NOT NULL DEFAULT 0,
            messages_elected_user integer NOT NULL DEFAULT 0,
            messages_other_users integer NOT NULL DEFAULT 0,
            sentence_id SERIAL NOT NULL,
            sentence_sub_type smallint,
            sentence_text text,
            sentence_difficulty smallint,
            sentence_correct_answers text ARRAY,
            sentence_error_words text ARRAY,
            CONSTRAINT sentence_correction_adaptive_data_student_id_fkey FOREIGN KEY (student_id)
                REFERENCES {schema}.student (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE,
            CONSTRAINT sentence_correction_adaptive_data_sentence_id_fkey FOREIGN KEY (sentence_id)
                REFERENCES {schema}.sentence_correction_data (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
        )
        WITH (
            OIDS = FALSE
        )
        TABLESPACE pg_default;
        ALTER TABLE {schema}.sentence_correction_adaptive_data
            OWNER to {user};
        """).format(
            schema=sql.Identifier(schema),
            user=sql.Identifier(conn.info.user)
        )
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    logger.info(
            (
                'Created sentence correction '
                'adaptive data table.'
            )
        )

def _create_vocabulary_guessing_adaptive_data_table(
    conn: 'connection',
    schema: str
) -> None:
    """
    Creates the vocabulary guessing adaptive data table.
    """
    logger.info(
            (
                'Creating vocabulary guessing '
                'adaptive data table.'
            )
        )
    query = sql.SQL("""
        CREATE TABLE {schema}.vocabulary_guessing_adaptive_data
        (
            id SERIAL PRIMARY KEY,
            student_id integer NOT NULL,
            group_id integer NOT NULL,
            turn_start timestamp NOT NULL,
            turn_duration interval NOT NULL,
            correct boolean NOT NULL DEFAULT FALSE,
            skipped boolean NOT NULL DEFAULT FALSE,
            messages_elected_user integer NOT NULL DEFAULT 0,
            messages_other_users integer NOT NULL DEFAULT 0,
            description_texts text ARRAY,
            vocab_id integer,
            vocab_sub_type smallint,
            vocab_word text NOT NULL,
            vocab_difficulty smallint,
            CONSTRAINT vocabulary_guessing_adaptive_data_student_id_fkey FOREIGN KEY (student_id)
                REFERENCES {schema}.student (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
        )
        WITH (
            OIDS = FALSE
        )
        TABLESPACE pg_default;

        ALTER TABLE {schema}.vocabulary_guessing_adaptive_data
            OWNER to {user};
        """).format(
            schema=sql.Identifier(schema),
            user=sql.Identifier(conn.info.user)
        )
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    logger.info(
            (
                'Created vocabulary guessing '
                'adaptive data table.'
            )
        )

def _create_sentence_correction_adaptive_data_trigger(
    conn: 'connection',
    schema: str
) -> None:
    """
    Creates a trigger function for the sentence correction adaptive
    data table. The trigger function will automatically insert
    sentence item data when provided with a sentence ID.
    """
    logger.info(
            (
                'Creating sentence correction '
                'adaptive data trigger.'
            )
        )
    query = sql.SQL("""
        CREATE OR REPLACE FUNCTION {schema}.get_sentence_correction_data()
            RETURNS TRIGGER
            AS
        $BODY$
        BEGIN
            SELECT sub_type, difficulty_level, sentence_corpus, correct_answers, error_words
            INTO NEW.sentence_sub_type, NEW.sentence_difficulty, NEW.sentence_text, NEW.sentence_correct_answers, NEW.sentence_error_words
            FROM {schema}.sentence_correction_data
            WHERE id = NEW.sentence_id;
            RETURN NEW;
        END;
        $BODY$
        LANGUAGE PLPGSQL;

        CREATE TRIGGER copy_sentence_correction_data
        BEFORE INSERT
            ON {schema}.sentence_correction_adaptive_data
            FOR EACH ROW
            EXECUTE PROCEDURE {schema}.get_sentence_correction_data();
        """).format(schema=sql.Identifier(schema))
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    logger.info(
            (
                'Created sentence correction '
                'adaptive data trigger.'
            )
        )

def _create_vocabulary_guessing_adaptive_data_trigger(
    conn: 'connection',
    schema: str
) -> None:
    """
    Creates a trigger function for the vocabulary guessing
    adaptive data table. The trigger function will automaticaly
    insert vocabulary item data when provided with a
    vocabulary word.
    """
    logger.info(
            (
                'Creating vocabulary guessing '
                'adaptive data trigger.'
            )
        )
    query = sql.SQL("""
        CREATE OR REPLACE FUNCTION {schema}.get_vocab_guessing_data()
            RETURNS TRIGGER
            AS
        $BODY$
        BEGIN
            SELECT sub_type, id, difficulty
            INTO NEW.vocab_sub_type, NEW.vocab_id, NEW.vocab_difficulty
            FROM {schema}.vocabulary_guessing_data
            WHERE word = NEW.vocab_word;
            RETURN NEW;
        END;
        $BODY$
        LANGUAGE PLPGSQL;

        CREATE TRIGGER copy_vocab_guessing_data
        BEFORE INSERT
            ON {schema}.vocabulary_guessing_adaptive_data
            FOR EACH ROW
            EXECUTE PROCEDURE {schema}.get_vocab_guessing_data();
        """).format(schema=sql.Identifier(schema))
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    logger.info(
            (
                'Created vocabulary guessing '
                'adaptive data trigger.'
            )
        )


def _create_discussion_table(conn, schema):
    '''
    Creates the discussion task data table.

    Args:
        conn (connection): The connection that is used to create the table.
        schema (str): The schema in which the table should be created.
    '''
    query = """
        CREATE TABLE {schema}.discussion_data
        (
            id serial NOT NULL,
            topic character varying(50) NOT NULL,
            proficiency_domain integer NOT NULL,
            discussion_text character varying NOT NULL,
            difficulty integer NOT NULL,
            questions character varying[] NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT proficiency_domain_fkey FOREIGN KEY (proficiency_domain)
                REFERENCES {schema}.proficiency_info (proficiency_id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
        )
        WITH (
            OIDS = FALSE
        );

        ALTER TABLE {schema}.discussion_data
            OWNER to PUT_YOUR_DB_CONNECTION_USER_HERE;
    """
    # Format the query.
    query = sql.SQL(
            query
        ).format(
            schema=sql.Identifier(schema)
        )
    # Get cursor and execute query.
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    logger.info('Created the discussion task data table.')


def _insert_discussion_data(conn, file_location: str):
    '''
    Inserts the data for the discussion task.
    '''
    # read in the csv file and transform it to a list of tuples
    df = pd.read_csv(file_location)
    data = list(df.itertuples(index=False, name=None))
    cur = conn.cursor()
    insert_query = (
            'INSERT INTO discussion_data (id, topic, proficiency_domain, '
            'discussion_text, difficulty, questions) VALUES %s'
        )
    execute_values(cur, insert_query, data, page_size=1000)
    cur.close()


def _create_discussion_adaptive_data_table(
    conn: 'connection',
    schema: str
) -> None:
    '''
    Creates the discussion task adaptive data table.
    '''
    logger.info(
            (
                'Creating discussion task '
                'adaptive data table.'
            )
        )
    query = sql.SQL("""
        CREATE TABLE {schema}.discussion_adaptive_data
        (
            id SERIAL PRIMARY KEY,
            student_id integer NOT NULL,
            group_id integer NOT NULL,
            discussion_start timestamp NOT NULL,
            discussion_duration interval NOT NULL,
            topic_easy_to_understand boolean NOT NULL DEFAULT FALSE,
            learned_something boolean NOT NULL DEFAULT FALSE,
            group_performance_rating integer NOT NULL DEFAULT 0,
            n_discussion_words integer NOT NULL DEFAULT 0,
            discussion_text_id integer,
            CONSTRAINT discussion_adaptive_data_student_id_fkey FOREIGN KEY (student_id)
                REFERENCES {schema}.student (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
        )
        WITH (
            OIDS = FALSE
        )
        TABLESPACE pg_default;

        ALTER TABLE {schema}.discussion_adaptive_data
            OWNER to {user};
        """).format(
            schema=sql.Identifier(schema),
            user=sql.Identifier(conn.info.user)
        )
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    logger.info(
            (
                'Created discussion task '
                'adaptive data table.'
            )
        )
