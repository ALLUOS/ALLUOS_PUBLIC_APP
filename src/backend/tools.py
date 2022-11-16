# This contains any helper functions that might be useful in more than one task
import random
import json
import regex as re


def random_list_index(list):
    """ 
    Returns a random integer in the range between 0 and the length of the list
    """
    return random.randrange(len(list))

# Function to load all phrases from phrase json


def load_phrases(filepath):
    print("Loading phrases from:", filepath)
    with open(filepath, 'r', encoding="utf8") as filehandle:
        return json.load(filehandle)

# Function to capitalize the first letter of a string and leave the rest as it is


def capitalize_string(s):
    # Convert string to list
    s_list = list(s)
    # Make sure first character is uppercase
    s_list[0] = s_list[0].upper()
    # Convert back and return result
    return "".join(s_list)


def deEmojify(text):
    """
    removes all Unicodes from a string
    """
    str_en = text.encode("ascii", "ignore")
    str_de = str_en.decode()
    return str_de
