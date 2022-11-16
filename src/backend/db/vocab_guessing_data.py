import psycopg2
import pandas as pd
import numpy as np
import random
from .connection import read_query_into_df
from ..entities.word import Word
from ..adaptability.proficiency import Vocabulary
import re

# Store last id of word
last_id = None


def get_db_sub_type_id(sub_type):
    """
    Returns the id that identifies a sub_type in the database
    """
    return sub_type.value


def extract_sub_types(db_id):
    """
    Returns all sub-types of the word as a list of the corresponding enum classes
    """
    # Make a list of single Vocabulary object from the ID of the subtask
    return [Vocabulary(db_id)]


def get_random_word_based_on_sub_type_and_difficulty(sub_type, difficulty):
    # TODO add difficulty to selection
    global last_id
    # Select sub_type string based on enum
    sub_type_id = get_db_sub_type_id(sub_type)
    # Execute select database statement # TODO use sub_type_id in selection query
    query = """SELECT * FROM vocabulary_guessing_data WHERE sub_type = %s AND difficulty = %s ORDER BY RANDOM() LIMIT 1;"""
    df = read_query_into_df(query, params=[sub_type_id, difficulty])
    # print(sub_type_id)
    # print(difficulty)
    # print(df)
    # Check if that word was selected before
    new_id = df["id"].values[0]
    # TODO: We need to get the last id for the group here not the last selected in general
    if new_id == last_id:
        return get_random_word_based_on_sub_type_and_difficulty(
            sub_type, difficulty)
    else:
        last_id = new_id
        # Extract sub-types as a list of sub-type enums
        sub_types = extract_sub_types(df['sub_type'][0])
        # Parse data into word object
        return Word(word=df['word'][0], sub_types=sub_types)
