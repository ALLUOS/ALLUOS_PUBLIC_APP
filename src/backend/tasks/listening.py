import logging
import random
import time
import statistics as stats
import datetime
from typing import Dict
import json
from .base_task import Task
# from ..db.task import get_task_by_name
from ..room_manager_storage import get_room_manager_of_group
from ..tools import load_phrases
from ..db.student_proficiency import update_student_proficiency
from ..db.student_data import update_student_data
from ...backend.adaptability.selection import select_sub_type
from ..db.student_proficiency import update_student_proficiency
from ..adaptability.proficiency import Others
from random import randint, shuffle


task_name = 'listening'
logger = logging.getLogger(__name__)


# Function to initialize phrases
phrase_dict = {}


def set_listening_task_phrases(config: dict):
    global phrase_dict
    # Get filepaths from config
    task_phrases_filepath = config['listening_task']
    common_phrases_filepath = config['common']
    # Merge both dictionaries (in case of duplicates, take the task specific one -> this one should be on the right)
    phrase_dict = {
        **load_phrases(common_phrases_filepath),
        **load_phrases(task_phrases_filepath)}


def get_phrase(phrase: str):
    return random.choice(phrase_dict[phrase])


class Listening(Task):

    topic = None

    iterator = 0  # number of topics that where send to this team

    possible_topics = []  # possible topics for this difficulty
    unasked_persons = ["P1", "P2", "P3"]
    answering_options = None
    correct_answer = None
    points = 0
    question = ["Question1", "CorrectAnswer1", [
        "FalseAnswer11", "FalseAnswer12", "FalseAnswer13"]]
    remaining_questions = [
        ["Question1", "CorrectAnswer1", ["FalseAnswer11", "FalseAnswer12", "FalseAnswer13"]],
        ["Question2", "CorrectAnswer2", ["FalseAnswer21", "FalseAnswer22", "FalseAnswer23"]],
        ["Question3", "CorrectAnswer3", ["FalseAnswer31", "FalseAnswer32", "FalseAnswer33"]]]

    questions_for_this_topic = [
        ["Question1", "CorrectAnswer1", ["FalseAnswer11", "FalseAnswer12", "FalseAnswer13"]],
        ["Question2", "CorrectAnswer2", ["FalseAnswer21", "FalseAnswer22", "FalseAnswer23"]],
        ["Question3", "CorrectAnswer3", ["FalseAnswer31", "FalseAnswer32", "FalseAnswer33"]]]
    person_who_answers = None

    # defines if the next message by the selected user is perceived as the answer
    answer_mode = False

    def __init__(self, users: list, difficulty: int):
        self.all_users = users
        self.difficulty = difficulty
        self.set_answer_mode(False)
        # Loading the possible topics from the json
        with open("./data/tasks/listening/topics.json", 'r') as filehandle:
            json_file_dict = {**json.load(filehandle)}
            self.possible_topics += [key for key in json_file_dict]

        try:
            with open("./data/audio/listening_task/A2-House-Viewing.mp3") as f:
                print("The Audio for this task was checked for its existance")
        except FileNotFoundError:
            print(
                "The audio-files of this task do not seem to be in this path: ./data/audio/listening_task/")
            print(
                "download them from: https://drive.google.com/drive/folders/1khMdHilTfUGsD_hvYioayLX67nB0KTqi")

    # getter and setter for basically everything.

    def get_person_who_answers(self):
        return self.person_who_answers

    def get_task_instructions(self):
        return phrase_dict['Task instruction']

    def get_answering_options(self):
        return self.answering_options

    def set_answer_mode(self, new):
        self.answer_mode = new

    def get_answer_mode(self):
        return self.answer_mode

    def get_correct_answer(self):
        return self.correct_answer

    def get_iterator(self):
        return self.iterator

    def increase_iterator(self):
        self.iterator += 1

    def get_points(self):
        return self.points

    def increase_points(self):
        self.points += 1

    def get_remaining_questions(self):
        return self.remaining_questions

    def get_topic(self):
        return self.topic

    def has_everyone_been_asked(self):
        """checks if every user in the group has been asked."""
        return(len(self.unasked_persons) == 0)

    def choose_a_topic(self):
        """Selects a Topic for the task-iteration."""
        # Fill the list of possible topics

        # choose a topic
        r = randint(0, len(self.possible_topics)-1)
        topicname = self.possible_topics[r]
        # delete the topic from the list, so that it does not show up later

        # Get the questions for this Topic
        with open("./data/tasks/listening/topics.json", 'r') as filehandle:
            json_file_dict = {**json.load(filehandle)}
            self.questions_for_this_topic = json_file_dict[topicname][
                "questions"]
            self.topic = json_file_dict[topicname]
        self.possible_topics.remove(topicname)

        self.remaining_questions = self.questions_for_this_topic[:]

        return self.topic

    def get_audio(self, topic: Dict):
        """
        returns the name of the audio-file
        """
        return topic["filename"]

    def choose_a_question(self, topic: dict):
        # choose a question
        self.question = self.remaining_questions[randint(
            0, len(self.remaining_questions)-1)]

        self.correct_answer = self.question[1]
        self.answering_options = [self.correct_answer]+self.question[2]
        shuffle(self.answering_options)
        # remove question to avoid double questioning
        self.remaining_questions.remove(self.question)

        return self.question[0]

    def reset_unasked_persons(self, group_chat_id: str):
        # Get a list of all participants
        group_room_manager = get_room_manager_of_group(group_chat_id)
        self.unasked_persons = group_room_manager.get_joined_student_list()

    def choose_a_person(self):
        # Choose a person who answers
        # Get a list of all participants who have not answered a question
        unasked_persons = self.unasked_persons

        # choose a person
        self.person_who_answers = unasked_persons[randint(
            0, len(unasked_persons)-1)]
        # remove the person from the list of possible candidates
        unasked_persons.remove(self.person_who_answers)

        self.unasked_persons = unasked_persons
        return self.person_who_answers

    def evaluate_Elias_Freedom(self, group_chat_id):
        """
        check wether the group has collected the points to free elias
        """
        group_room_manager = get_room_manager_of_group(group_chat_id)
        max_points = len(group_room_manager.get_joined_student_list())*3
        current_points = self.points
        if current_points >= 0.66*max_points:
            return True
        else:
            return False


# To avoid multiple instances of the Task they are packaged within singeltons.
singeltons = {}


def get_listening_task_of_group(group_chat_id: str) -> Listening:
    """
    Returns the ListeningTask of the group.
    Args:
        group_chat_id (str): The id of the group chat from telegram.
    Returns:
        The ListeningTask instance that is used by the group.
    """
    group_singelton = singeltons.get(group_chat_id)
    if not group_singelton:
        # get the students that participate in the task
        active_users = get_room_manager_of_group(
            group_chat_id).get_joined_student_list()
        # alternatively
        # group_singelton = create_listening_task(active_users, 3, number of iterations)
        group_singelton = Listening(users=active_users, difficulty=3)
        singeltons[group_chat_id] = group_singelton
    return group_singelton


def remove_listening_task_of_group(group_chat_id: str):
    """
    Removes the listenigDescription of the group from the list of singeltons.
    Args:
        group_chat_id (str): The id of the group chat from telegram.
    """
    # Save data to the database
    for student in get_room_manager_of_group(group_chat_id).get_joined_student_list():
        update_student_proficiency(student)
        update_student_data(student)
    # Remove singleton
    singeltons.pop(group_chat_id, None)
