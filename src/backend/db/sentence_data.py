import psycopg2
import pandas as pd
import numpy as np
import random
from .connection import read_query_into_df
from ..entities.sentence import Sentence
from ..adaptability.proficiency import Grammar
import re

# Store last id of sentence
last_id = None


def get_test_data():
    query = """SELECT * FROM sentence_correction_data ORDER BY RANDOM() LIMIT 10"""
    return read_query_into_df(query)


def get_db_sub_type_id(sub_type):
    """
    Returns the id that identifies a sub_type in the database
    """
    return sub_type.value


def extract_sub_types(db_id):
    """
    Returns all sub-types of the sentence as a list of the corresponding enum classes
    """
    # Make a list of single Grammar object from the ID of the subtask
    return [Grammar(db_id)]


def get_sentence_information_from_df(row):
    """
    Parses the information from the database into sentence corpus, one error word and one correct answer
    """
    sub_types = extract_sub_types(row['sub_type'].values[0])
    error_words = row['error_words'].values[0]
    sentence = row['sentence_corpus'].values[0]
    selected_error_word = random.choice(error_words)
    correct_answers = row['correct_answers'].values[0]
    return sentence, selected_error_word, correct_answers, sub_types


def get_random_sentence_based_on_sub_type_and_difficulty(sub_type, difficulty):
    global last_id
    # Select sub_type string based on enum
    sub_type_id = get_db_sub_type_id(sub_type)
    # Execute select database statement # TODO use sub_type_id in selection query
    query = """SELECT * FROM sentence_correction_data WHERE sub_type = %s AND difficulty_level = %s ORDER BY RANDOM() LIMIT 1;"""
    #print("send query with subtype:" + str(sub_type_id) + ", difficulty: " + str(difficulty))
    df = read_query_into_df(query, params=[sub_type_id, difficulty])
    # print(df)
    # Check if that sentence was selected before
    new_id = df["id"][0]
    # TODO: We need to get the last id for the group here not the last selected in general
    if new_id == last_id:
        return get_random_sentence_based_on_sub_type_and_difficulty(
            sub_type, difficulty)
    else:
        last_id = new_id
        # Extract all information of sentence database record
        sentence, selected_error_word, correct_answers, sub_types = get_sentence_information_from_df(
            df)
        # Parse data into sentence object (the object randomly instantiates as correct or incorrect)
        return Sentence(
            sentence=sentence,
            error_word=selected_error_word,
            error_corrections=correct_answers,
            sub_types=sub_types,
            idx=last_id
        )
