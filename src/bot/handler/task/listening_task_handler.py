from telegram import (Update, ReplyKeyboardMarkup,
                      InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (
    CommandHandler, MessageHandler, Filters, ConversationHandler,
    CallbackContext)

from src.misc.debug_mode import is_debug_mode_active
from ....backend.tasks.listening import get_listening_task_of_group, remove_listening_task_of_group, get_phrase
from ..room_handler import end_task_group, get_room_manager_of_group, remove_room_manager_of_group, prompt_task_selection
from .. import state
from ...util import get_gif_link, get_group_chat_id, send_animation, send_message, create_keyboard_markup, send_audio
from random import randint, shuffle
import logging
import time

from src.backend.tasks import listening

logger = logging.getLogger(__name__)
YesNo_MarkUp = create_keyboard_markup(['Yes', 'No'])


def task_selection(update: Update, context: CallbackContext):
    """
    Evaluates task selection messages.
    If the listening-task was requested by the right user,
    show the task-description, otherwise return to the task selection
    """
    # Get room manager
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    # Get selected user who has to chose the task
    selected_usr = group_room_manager.get_selected_user()
    # Check if the message is from the selected user
    if update.message.from_user.username == selected_usr:
        # Set task in room manager
        group_room_manager.next_task("listening")
        return show_listening_task_description(update, context)
    else:
        # Wait for message from the correct user -> go back to task selection
        return state.LISTENING_SEL_WRONG_USER


def show_listening_task_description(update: Update, context: CallbackContext):
    """
    sends the task instructions of the listening task.
    It starts the next iteration.
    """
    # get the listening task of this group
    group_chat_id = get_group_chat_id(update)
    listening_task = get_listening_task_of_group(group_chat_id)
    send_message(get_phrase("story"), update, context)
    send_message(get_phrase('Task instruction'),
                 update, context, text_markup=True)
    gif_url = get_gif_link("think")
    send_animation(gif_url, update, context)

    return start_iteration_circle(update, context)


def start_iteration_circle(update: Update, context: CallbackContext):
    """
    sends an audio file and asks a question. There are 3 iteration circles.
    """
    group_chat_id = get_group_chat_id(update)
    listening_task = get_listening_task_of_group(group_chat_id)
    listening_task.increase_iterator()

    topic = listening_task.choose_a_topic()
    # send the audio-file
    audiopath = "./data/audio/listening_task/"
    filename = listening_task.get_audio(topic)
    send_audio(audiopath+filename, update, context)

    if not(is_debug_mode_active()):
        time.sleep(60)

    listening_task.reset_unasked_persons(group_chat_id)

    return start_questioning_circle(update, context)


def start_questioning_circle(update: Update, context: CallbackContext):
    """
    Sends a question to a specific person. Offers Extension if you need more time. Is called once per User per Iteration
    """
    group_chat_id = get_group_chat_id(update)
    listening_task = get_listening_task_of_group(group_chat_id)
    topic = listening_task.get_topic()
    person_who_answers = listening_task.choose_a_person()

    question = listening_task.choose_a_question(topic)
    person_who_answers = listening_task.get_person_who_answers().get_telegram_id()
    send_message(question+" Please answer @{}".format(person_who_answers),
                 update, context)
    send_answering_options(update, context)

    # creating and sending the inline Keyboard
    keyboard = [
        [
            InlineKeyboardButton("I want to answer now!", callback_data='NOW'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    waiting_time = 90
    if is_debug_mode_active():
        waiting_time = 15
    send_message(get_phrase("discuss_timer").format(str(waiting_time)),
                 update, context, reply_markup=reply_markup)

    context.job_queue.run_once(time_is_up, when=waiting_time, context=update)
    return state.DISCUSSION_TIME


def check_person_who_answers(update: Update) -> bool:
    """checks wether the person who did send the last update, was the person whose turn it was"""
    listening_task = get_listening_task_of_group(
        get_group_chat_id(
            update))

    update_dict = eval(str(update))

    username = str(update_dict['callback_query']['from']['username'])
    telegram_id = str(listening_task.get_person_who_answers().get_telegram_id())
    #print("The person who pressed the button was:", username)
    #print("The person who is allowed to press the button is:", telegram_id)

    return username == telegram_id


def answer_early_button(update: Update, context: CallbackContext) -> None:
    """
    Manages button-clicks on the Inline-Buttons. 

    When the Button "NOW" is clicked, the answer-mode is set to true,
    resulting in the next sentence by the user is perceived as answer.
    """
    query = update.callback_query
    query.answer()
    choice = query.data
    group_chat_id = get_group_chat_id(update)
    listening_task = get_listening_task_of_group(group_chat_id)

    if choice == "NOW":
        # First check if message was sent from the selected user
        # if the correct person clicked the button, we get an answer.
        if check_person_who_answers(update):
            listening_task.set_answer_mode(True)
            demand_answer(context, update)
        else:
            send_message(
                "Only the person who is supposed to answer, is allowed to press this button.",
                update, context)


def time_is_up(context: CallbackContext):
    """
    Sends out a message, that the time is up and that the user should answer now. It also changes the answer mode.
    """
    job = context.job
    update = job.context

    group_chat_id = get_group_chat_id(update)
    listening_task = get_listening_task_of_group(group_chat_id)
    listening_task.set_answer_mode(True)
    demand_answer(context, update)


def is_answer_mode(update: Update, context: CallbackContext):
    """
    checks wether the next answer by the selected user is perceived as an answer to the question, or not.
    """
    group_chat_id = get_group_chat_id(update)
    listening_task = get_listening_task_of_group(group_chat_id)
    return listening_task.get_answer_mode()


def check_selected_user(update: Update):
    """
    Checks if the User who answered is the person that is supposed to answer
    """
    listening_task = get_listening_task_of_group(get_group_chat_id(update))
    return update.message.from_user.username == listening_task.get_person_who_answers().get_telegram_id()


def demand_answer(context: CallbackContext, update: Update):
    """
    The User has to answer now. Therefore he gets all the possible answers as a keyboard.
    """
    if update == None:
        job = context.job
        update = job.context
    print("demand_answer")
    group_chat_id = get_group_chat_id(update)
    listening_task = get_listening_task_of_group(group_chat_id)
    person_who_answers = listening_task.get_person_who_answers().get_telegram_id()
    msg = ""
    msg += get_phrase("please_answer").format(
        person_who_answers)
    answer_options = listening_task.get_answering_options()
    answer_options = [[answer] for answer in answer_options]

    if is_debug_mode_active():
        print("correct_answer:", listening_task.get_correct_answer())

    Keyboard = ReplyKeyboardMarkup(
        answer_options, resize_keyboard=True, one_time_keyboard=True,
        selective=True)
    send_message(msg, update, context, reply_markup=Keyboard)


def send_answering_options(update: Update, context: CallbackContext):
    """
    Send out the Answering Options in a nice way.
    """
    group_chat_id = get_group_chat_id(update)
    listening_task = get_listening_task_of_group(group_chat_id)
    answering_options = listening_task.get_answering_options()
    msg = ""
    #letters = ["A", "B", "C", "D", "E"]
    for i in range(0, len(answering_options)):
        #msg += letters[i]+": "
        msg += answering_options[i]+"\n"
    send_message(msg, update, context, delay=False)
    return answering_options


def evaluate_answer(update: Update, context: CallbackContext):
    """
    If the task is in answer-mode:
    checks the answer by the correct user. If it is correct the user gets a point.
    """

    # only accept answers, when the bot is in answer_mode
    if not(is_answer_mode(update, context)):
        return state.DISCUSSION_TIME

    # stops the counter, that is running in the background.
    remove_running_jobs(context)

    # if the correct user answers:
    if check_selected_user(update):
        group_chat_id = get_group_chat_id(update)
        listening_task = get_listening_task_of_group(group_chat_id)

        # Deactivate the answer_mode
        listening_task.set_answer_mode(False)

        # get the given answer
        given_answer = update.message.text

        # get the correct answer
        correct_answer = listening_task.get_correct_answer()
        print("The User gave the answer:", given_answer,
              "-", correct_answer, "is the correct answer")

        # send answers depending on the correctnes of the answer
        if given_answer == correct_answer:
            send_message(
                get_phrase("correct"),
                update, context)
            listening_task.increase_points()
        else:
            send_message(
                get_phrase("incorrect"),
                update, context)

        return end_iteration(update, context)
    else:
        return state.DISCUSSION_TIME


def end_iteration(update: Update, context: CallbackContext):
    """
    If Everybody got a question --> New Topic
    Else --> New Question for next person
    If we allready had 3 Topics or Enough Points to win--> Task completed
    Else --> New Topic
    """
    group_chat_id = get_group_chat_id(update)
    listening_task = get_listening_task_of_group(group_chat_id)

    # check if everybody has been asked a question about this topic
    if listening_task.has_everyone_been_asked():
        send_message(get_phrase("round_completed"),
                     update, context)
    else:
        # otherwise start the next round of questioning
        remaining_questions = listening_task.get_remaining_questions()
        return start_questioning_circle(update, context)

    # check if the iterations are completed
    # task is complete when 3 Iterations are done or enough Points are reached.
    if listening_task.get_iterator() == 3 or listening_task.evaluate_Elias_Freedom(group_chat_id):
        msg = get_phrase("task_completed").format(
            str(listening_task.get_points()))+" "
        success = False
        if listening_task.evaluate_Elias_Freedom(group_chat_id):
            msg += " "+get_phrase("elias_is_free")
            success = True
        else:
            msg += get_phrase("elias_stays")
        send_message(msg, update, context)
        return end_task(update, context, success)
    else:  # otherwise start the next iteration
        return start_iteration_circle(update, context)


def end_task(update: Update, context: CallbackContext, success: bool):
    """ends the listening task."""
    logger.info('Test information: End of Listening task')
    # Remove existing jobs if there are any
    remove_running_jobs(context)

    # Remove the listening task from the list of possible open tasks.
    remove_listening_task_of_group(get_group_chat_id(update))

    # End the task -> Send dialogue and go to password entering
    return prompt_task_selection(
        update, context,
        get_room_manager_of_group(get_group_chat_id(update)))


def remove_running_jobs(context: CallbackContext):
    for job in context.job_queue.jobs():
        job.schedule_removal()


def stop_task(update: Update, context: CallbackContext):
    # Log info about proficiency
    logger.info('Test information: End of Listening task')
    listening_task = get_listening_task_of_group(get_group_chat_id(update))
    # listening_task.log_proficiencies()#TODO implement
    # Remove existing jobs if there are any
    remove_running_jobs(context)

    # remove listening task from the list of possible tasks
    remove_listening_task_of_group(get_group_chat_id(update))

    # Remove the room manager
    remove_room_manager_of_group(get_group_chat_id(update))
    # Send goodbye
    update.message.reply_text(
        text='Goodbye. To start again write /start.', quote=False)

    # Return end state
    return state.DISCUSS_STOP
