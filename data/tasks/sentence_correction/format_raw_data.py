import pandas as pd
import numpy as np
import re 
import random
import os


# Set filepath to data that we want to modify
input_filepath = os.getcwd() + r'\\data\\tasks\sentence_correction\\raw_data.csv'

# Set filepath to output data
output_filepath = os.getcwd() + r'\\data\\tasks\sentence_correction\\task_data.csv'

#error_words_extraction extracts the words that are there in the brackets in the sentence and stores them in a new column
def error_words_extraction(dataframe): 
    b = []
    a = dataframe['sentence_corpus']
    for i in range(len(a)):
        substring = re.search('{(.+?)}', a[i])
        substring = substring.group(0)
        b.append(substring)
    dataframe['error_words'] = b    
    return(data)

#empty_spaces_corpus removes the words inside the brackets in the sentence and creates blank brackets
def empty_spaces_corpus(dataframe): 
    refined = []
    a = dataframe['sentence_corpus']
    for i in range(len(a)): 
        refined.append(re.sub(r'\{.*\}', '{}', a[i]))
    dataframe['sentence_corpus'] = refined
    return(data)

#data_reduction removes the error_index column, convers the difficulty_level and error_type columns to numberic
def data_reduction(dataframe):
    dataframe['difficulty_level'] = dataframe['difficulty_level'].map({'beginner': '1','intermediate': '2','advanced': '3'}).fillna(dataframe['difficulty_level'])
    dataframe['sub_type'] = dataframe['sub_type'].map({
    'To-infinitive': '4', 'Present Perfect':'2', 'Relative Clauses': '8', 'negation':'9',
           'Subjunctive': '12', 'verb + to-infinitive':'4', 'Gerunds':'6',
           'verb + preposition':'10', 'Adverbs':'11'}).fillna(dataframe['sub_type'])
    return(dataframe)

# Converts a given value to a list by adding parantheses for database upload
def convert_to_list(val):
    # Check if column is list already
    if val[0] == '{' and val [-1] == '}':
        return val
    else:
        return '{' + val + '}'

# Load the data into dataframe and set the column names
data = pd.read_csv(input_filepath)
column_names = ['sub_type', 'difficulty_level', 'sentence_corpus', 'correct_answers']
data.columns = column_names

# Apply all transformations
data = error_words_extraction(data)
data = empty_spaces_corpus(data)
data = data_reduction(data)
data.correct_answers = data.correct_answers.apply(convert_to_list)

# Write output to csv file
data.to_csv(output_filepath, index = False)