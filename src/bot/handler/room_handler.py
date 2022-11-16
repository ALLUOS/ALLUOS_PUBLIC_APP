from ast import Str
from src.misc.debug_mode import activate_debug
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove)
from telegram.ext import (CallbackContext)
import random
import logging
import json
import emoji

from ...backend.room_manager_storage import get_room_manager_of_group, remove_room_manager_of_group
from ...backend.room_manager import RoomManager
from . import state

from ..util import get_group_chat_id, create_keyboard_markup, send_message, send_animation, get_gif_link, get_sticker_id, send_sticker, transform_codeword_to_emoji
from ...backend.adaptability import path_selection
from ...backend.entities.paths import PathCollection, Path
from ...backend.tools import load_phrases

#from src.misc.debug_mode import activate_debug

logger = logging.getLogger(__name__)

# Empty phrase dictionary and emojis
phrases = {}
emoji_elias = ""
emoji_harriet = ""


# Keyboard for ready check
ready_check_keyboard = create_keyboard_markup(
    [emoji.emojize('✔️Yes, let\'s go!'),
     emoji.emojize('❌No, not yet!')],
    selective=False)

# Keyboard for /stop
stop_keyboard = create_keyboard_markup(
    ["/start"],
    selective=False)


def set_sentence_correction_task_phrases(config):
    global phrases, emoji_elias, emoji_harriet
    # Get filepaths from config
    room_manager_phrases_filepath = config['room_manager_phrases']
    # Get scenario from config
    scenario = config['story_scenario']
    # Load the dictionary
    all_phrases = load_phrases(room_manager_phrases_filepath)
    # Select scenario
    phrases = all_phrases[scenario]
    # Store emojis for elias and harriet
    emoji_elias = phrases["emojis"]["elias"]
    emoji_harriet = phrases["emojis"]["harriet"]


def _get_task_choice_keyboard(group_room_manager) -> ReplyKeyboardMarkup:
    """
    Creates the task choice keyboard for the given number of participants.

    Args:
        group_room_manager: The current group room manager

    Returns:
        The task choice keyboard with all tasks that can be started.
    """
    task_list = group_room_manager.get_available_tasks()
    if len(task_list) <= 0:
        print("There are no tasks left to do for this amount of people")
    name_list = [task.title() for task in task_list]
    return create_keyboard_markup(name_list)


def _get_random_telegram_id(list_of_students: list):
    """
    Returns a random telegram id of one of the provided students.
    """
    return random.choice(list_of_students).get_telegram_id()


def debug():
    send_message("Debugmode is now set to active")
    # activate_debug()
    return start_escape


def start_escape(update: Update, context: CallbackContext):

    intro_phrases = phrases["group_intro"]

    # Send messages from elias
    id = get_sticker_id("elias_waving")
    send_sticker(update, id)

    for msg in intro_phrases["elias"]:
        send_message(msg, update, context, speaker="elias")

    for narrator_intro_msg in intro_phrases["narrator"]:
        send_message(narrator_intro_msg, update, context)

    # Send messages from harriet
    id = get_sticker_id("harriet_basic")
    send_sticker(update, id)
    for msg in intro_phrases["harriet"]:
        send_message(msg, update, context, speaker="harriet")

    # Do ready check
    return _ask_for_readiness(update, context)


def _ask_for_readiness(update: Update, context: CallbackContext):

    # get the room manager for the group and reset readiness
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    group_room_manager.reset_joined_students()

    # ask the users whether they are ready or not
    msg = 'Okay, are you ready?'
    send_message(msg, update, context,
                 reply_markup=ready_check_keyboard, speaker="harriet")
    # Return waiting for readiness state
    return state.WAIT_FOR_USERS_TO_BE_READY


def button_manager(update: Update, context: CallbackContext):
    """
    Manages button-clicks on the Inline-Buttons. 

    When the Button "START" is clicked, the answer-mode is set to true,
    resulting in the next sentence by the user is perceived as answer.
    """
    query = update.callback_query
    query.answer()
    choice = query.data
    group_chat_id = get_group_chat_id(update)

    if choice == "START":
        # get the room manager for the group and reset readiness
        group_room_manager = get_room_manager_of_group(
            get_group_chat_id(update))
        # set the available tasks manually since it is not part of prompting task selection anymore
        # as it overwrites available tasks with all tasks applicable for group size
        group_room_manager.set_available_tasks()
        return prompt_task_selection(update, context, group_room_manager)


def prompt_task_selection(update, context, group_room_manager):
    # Get choice of tasks
    task_choice_keyboard = _get_task_choice_keyboard(group_room_manager)
    # Select random user to choose next task
    rnd_user = _get_random_telegram_id(
        group_room_manager.get_joined_student_list())
    rnd_user_txt = '@' + rnd_user
    # Store info in group manager
    group_room_manager.set_selected_user(rnd_user)
    # Prompt user about task selection
    msg = "{}, choose the task!".format(rnd_user_txt)
    send_message(msg, update, context,
                 reply_markup=task_choice_keyboard, speaker="harriet")
    # Return to task choice state
    return state.WAIT_FOR_TASK_SELECTION


def stop_group(update: Update, context: CallbackContext):
    # Remove the room manager
    remove_room_manager_of_group(get_group_chat_id(update))
    # Send goodbye
    print("The users stopped the bot using /stop")
    send_message(
        'Goodbye. To start again write /start.', update, context,
        reply_markup=create_keyboard_markup(["/start"]))
    # Return end state
    return state.END


def evaluate_readiness(update: Update, context: CallbackContext):
    # Get room manager
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    # Check if a new student was added
    was_student_added = group_room_manager.add_student_to_joined_list(
        update.effective_user.username)

    # how many people are in the group
    chat = update.effective_chat
    n_total = chat.get_members_count()

    print("there are", n_total, "people in this chat.")

    # Inform the user that they were added

    # if was_student_added:
    n_ready = group_room_manager.get_number_of_joined_students()
    print(str(n_ready), "people said, that they are ready.")
    print("it needs", str(n_total-2), "to get started")

    msg = ("✔️ "*n_ready) + ("❌ "*(n_total-n_ready-2))
    send_message(msg, update, context)

    # Check if we can start the task selection
    if group_room_manager.did_everyone_join():

        # Inform group that we are ready
        msg = "Great, we are ready!"
        send_message(msg, update, context, speaker="harriet")
        # set the available tasks manually since it is not part of prompting task selection anymore
        # as it overwrites available tasks with all tasks applicable for group siz
        group_room_manager.set_available_tasks()
        # Go to task selection
        return prompt_task_selection(update, context, group_room_manager)
    else:
        # creating and sending the inline Keyboard
        keyboard = [[
            InlineKeyboardButton(
                "We want to start without the missing players",
                callback_data='START'), ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        send_message(
            "There are still some players missing. If you want to play without them, press this button",
            update, context, reply_markup=reply_markup, delay=False)
        return state.WAIT_FOR_USERS_TO_BE_READY


def end_task_group(
        update: Update, context: CallbackContext, success: bool,
        state_success: int, state_fail: int, codeword: str = None):
    """
    Handles the ending of a task
    """
    # Get group manager
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    # Check which task that has ended
    cur_task_count = group_room_manager.get_current_task_count()
    # check if task is still repeatable
    # i.e. if repetition counter is less than 2 and the task was failed
    if (not success) and (group_room_manager._reps_counter[group_room_manager._current_task] < 2):
        # send messages containing info about repeatability of the task
        task_phrases = phrases["after_failed_first_task"]
        # send message from Harriet
        msg = task_phrases["harriet"]
        send_message(msg, update, context, speaker="harriet")
        # Send narrative info
        msg = task_phrases["narrator"]
        send_message(msg, update, context)

        # Send message from elias
        id = get_sticker_id("elias_sad")
        send_sticker(update, id)
        msg = task_phrases["elias"]
        send_message(msg, update, context, speaker="elias")
        # Go to task selection
        return prompt_task_selection(update, context, group_room_manager)
    else:
        # Handle storyline depending on which task has ended
        if cur_task_count == 1:
            after_task_1(group_room_manager, update, context, success, codeword)
        if cur_task_count == 2:
            after_task_2(group_room_manager, update, context, success, codeword)
        if cur_task_count == 3:
            after_task_3(group_room_manager, update, context, success, codeword)
        # especially handle the situation when first task was failed and cannot be repeated
        # and therefore entire mission is failed
        if cur_task_count <= 0:
            task_count_back_to_0(
                group_room_manager, update, context, success, codeword)

    # Return success or fail state
    if success:
        return state_success
    else:
        return state_fail


def task_count_back_to_0(
    group_room_manager: RoomManager,
    update: Update,
    context: CallbackContext,
    success: bool,
    codeword: str = None
):
    """
    Handle failure of very first task, without possibility to repeat it.
    """
    # Get phrase dictionary
    task_phrases = phrases["end"]["failure"]
    # Send message from elias
    msg = task_phrases["elias"]
    send_message(msg, update, context, speaker="elias")
    # Send narrative bits
    for msg in task_phrases["narrator"]:
        send_message(msg, update, context)
    # Send message from elias
    msg = task_phrases["elias_2"]
    send_message(msg, update, context, speaker="elias")
    # Restart story here if users want to
    _ask_for_restart_after_fail(update, context)


def after_task_1(group_room_manager: RoomManager, update: Update,
                 context: CallbackContext, success: bool, codeword: str = None):
    """
    Handles the ending of the first task
    """
    # Get phrase dictionary
    task_phrases = phrases["between_task_1_2"]
    # Check if task was successful
    if success:
        # Check if task was a discussion task -> we also need to send the code
        if group_room_manager.current_is_discussion_task():
            codeword = transform_codeword_to_emoji(str(codeword))
            msg = task_phrases["success_discussion"].format(codeword)
        else:
            msg = task_phrases["success"]
        # Send message from harriet
        id = get_sticker_id("harriet_party")
        send_sticker(update, id)
        send_message(msg, update, context, speaker="harriet")
        # Select random user to enter the password
        rnd_user = _get_random_telegram_id(
            group_room_manager.get_joined_student_list())
        rnd_user_txt = '@' + rnd_user
        # Store info in group manager
        group_room_manager.set_selected_user(rnd_user)
        # Display narrative info
        id = get_sticker_id("password_panel")
        send_sticker(update, id)

        for msg in task_phrases["password_prompt"]:
            send_message(msg.format(rnd_user_txt), update, context)
        # Store passcode in room manager
        group_room_manager.set_passcode(codeword)
    else:
        # Send failure message from harriet
        msg = task_phrases["failure"]["harriet"]
        send_message(msg, update, context, speaker="harriet")
        # Send narrative info
        msg = task_phrases["failure"]["narrator"]
        send_message(msg, update, context)

        # Send message from elias
        id = get_sticker_id("elias_sad")
        send_sticker(update, id)
        msg = task_phrases["failure"]["elias"]
        send_message(msg, update, context, speaker="elias")
        # Restart story here if users want to
        _ask_for_restart_after_fail(update, context)


def after_task_1_passcode(update: Update, context: CallbackContext):
    """
    Handles the story after the passcode has been correctly entered at the end of the first task
    """
    # Get phrase dictionary
    task_phrases = phrases["between_task_1_2"]
    # Send narrative bit
    for msg in task_phrases["correct_password"]:
        send_message(msg, update, context)
    # Send text from harriet
    msg = task_phrases["message_harriet"]
    send_message(msg, update, context, speaker="harriet")
    # Refer to path selection
    return prompt_task_selection(
        update, context,
        get_room_manager_of_group(get_group_chat_id(update)))


def after_task_2(group_room_manager: RoomManager, update: Update,
                 context: CallbackContext, success: bool, codeword: str = None):
    """
    Handles the ending of the second task
    """

    btw_task_2_3_phrases = phrases["between_task_2_3"]

    if success:

        # Check if task was a discussion task -> we also need to send the code
        narrator_msg = ""
        if group_room_manager.current_is_discussion_task():
            emojized_codeword = transform_codeword_to_emoji(str(codeword))
            narrator_msg = emoji.emojize(
                btw_task_2_3_phrases["success_discussion"].format(
                    emoji_harriet, emojized_codeword))
        else:
            narrator_msg = btw_task_2_3_phrases["success"]
        send_message(narrator_msg, update, context)

        # Select random user to enter the password
        rnd_user = _get_random_telegram_id(
            group_room_manager.get_joined_student_list())
        rnd_user_txt = '@' + rnd_user
        # Store info in group manager
        group_room_manager.set_selected_user(rnd_user)

        # Display narrative info
        id = get_sticker_id("password_panel")
        send_sticker(update, id)

        narrator_msg = btw_task_2_3_phrases["password_prompt"]
        send_message(narrator_msg.format(rnd_user_txt), update, context)

        # Store passcode in room manager
        group_room_manager.set_passcode(codeword)
    else:
        msg = btw_task_2_3_phrases["failure"]["harriet"]
        send_message(msg, update, context, speaker="harriet")

        narrator_msg = btw_task_2_3_phrases["failure"]["narrator"]
        send_message(narrator_msg, update, context)

        # Send message from elias
        id = get_sticker_id("elias_sad")
        send_sticker(update, id)

        msg = btw_task_2_3_phrases["failure"]["elias"]
        send_message(msg, update, context, speaker="elias")
        # Restart story here if users want to
        _ask_for_restart_after_fail(update, context)


def after_task_2_passcode(update: Update, context: CallbackContext):
    """
    Handles the story after the passcode has been correctly entered at the end of the second task
    """
    # Get phrase dictionary
    task_phrases = phrases["between_task_2_3"]
    # Send narrative bit
    for msg in task_phrases["correct_password"]:
        send_message(msg, update, context)
    # Send text from harriet
    msg = task_phrases["message_harriet"]
    send_message(msg, update, context, speaker="harriet")
    # Refer to path selection
    return prompt_task_selection(
        update, context,
        get_room_manager_of_group(get_group_chat_id(update)))


def after_task_3(group_room_manager: RoomManager, update: Update,
                 context: CallbackContext, success: bool, codeword: str = None):
    """
    Handles the ending of the third (and final) task
    """
    # Check if task was successful
    if success:
        # Get phrase dictionary
        task_phrases = phrases["end"]["success"]
        # Check if task was a discussion task -> we also need to send the code
        if group_room_manager.current_is_discussion_task():
            codeword = transform_codeword_to_emoji(str(codeword))
            msg = task_phrases["elias_discussion"].format(codeword)
        else:
            msg = task_phrases["elias"]
        # Send messsage from elias
        id = get_sticker_id("elias_party")
        send_sticker(update, id)
        send_message(msg, update, context, speaker="elias")
        # Select random user to enter the password
        rnd_user = _get_random_telegram_id(
            group_room_manager.get_joined_student_list())
        rnd_user_txt = '@' + rnd_user
        # Store info in group manager
        group_room_manager.set_selected_user(rnd_user)
        # Display narrative info
        get_sticker_id("password_panel")
        send_sticker(update, id)
        msg = task_phrases["password_prompt"]
        send_message(msg.format(rnd_user_txt), update, context)
        # Store passcode in room manager
        group_room_manager.set_passcode(codeword)
    else:
        # Get phrase dictionary
        task_phrases = phrases["end"]["failure"]
        # Send message from elias
        msg = task_phrases["elias"]
        send_message(msg, update, context, speaker="elias")
        # Send narrative bits
        for msg in task_phrases["narrator"]:
            send_message(msg, update, context)
        # Send message from elias
        msg = task_phrases["elias_2"]
        send_message(msg, update, context, speaker="elias")
        # Restart story here if users want to
        _ask_for_restart_after_fail(update, context)


def after_task_3_passcode(update: Update, context: CallbackContext):
    """
    Handles the story after the passcode has been correctly entered at the end of the third (and final) task
    """
    # Get phrase dictionary
    task_phrases = phrases["end"]["success"]
    # Send narrative info
    for msg in task_phrases["correct_password"]:
        send_message(msg, update, context)
    # Send message from Harriet
    msg = task_phrases["message_harriet"]
    # send a "lets talk: GIF"
    path_to_gif = get_gif_link("earth")
    send_animation(path_to_gif, update, context)
    # End the journey
    return stop_group(update, context)


def check_passcode(update: Update, context: CallbackContext):
    # Get room manager
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    # Get selected user
    selected_usr = group_room_manager.get_selected_user()
    # Check if message is from that user
    if update.message.from_user.username == selected_usr:
        # Check if password is correct
        if group_room_manager.get_passcode() in update.message.text:
            # Delegate to function based on current task
            cur_task_count = group_room_manager.get_current_task_count()
            if cur_task_count == 1:
                return after_task_1_passcode(update, context)
            if cur_task_count == 2:
                return after_task_2_passcode(update, context)
            if cur_task_count == 3:
                return after_task_3_passcode(update, context)
        elif update.message.text.isdecimal():  # check if the answer was/could have been the password. Since the passwords are all numbers, this can only be true then
            # Send info about incorrect password
            msg = random.choice(
                phrases["general"]["wrong_password"])
            send_message(msg, update, context)
    else:
        # Do not change the current state
        return None


def evaluate_restart(update: Update, context: CallbackContext):
    # Get group room manager
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    # Get user that answered
    user_telegram_id = update.message.from_user.username
    # Get answer
    is_answer_yes = update.message.text.lower() == "yes"
    # Update answer counter
    group_room_manager.update_restart_poll(is_answer_yes, user_telegram_id)
    # Check if the poll has ended (either if all active users have responded)
    if group_room_manager.all_users_responded_to_poll():
        # Check poll results
        if group_room_manager.get_poll_restart_result():
            # Reset list of eligible tasks
            group_room_manager.set_available_tasks()
            # Reset task counter
            group_room_manager.reset_current_task_count()
            group_room_manager.reset_reps_counter()
            # Send message for restarting
            msg = "Okay, let's try this again! Good luck!"
            send_message(msg, update, context, speaker="elias")
            # Ask for paths and then start over - PATHS DISABLED!
            # return ask_for_path(update, context)
        else:
            # End the application
            return stop_group(update, context)


def _ask_for_restart_after_fail(update: Update, context: CallbackContext):
    """
    Asks the users if they want to restart the mission after failure
    """
    # Reset poll
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    group_room_manager.reset_restart_poll()
    # Send poll asking users to restart
    msg = "Do you want to restart the escape?"
    restart_keyboard = create_keyboard_markup(["Yes", "No"], selective=False)
    send_message(msg, update, context, reply_markup=restart_keyboard)


def ask_for_path(update: Update, context: CallbackContext):
    """
    1. Select appropriate paths for the users to choose from
    2. Sends the users a message and a reply markup to choose a path for the next task
    Returns to PATH.SEL
    """
    # get the room manager for the group and the current task
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    current_task = group_room_manager.get_current_task()
    # ask the users for the paths they want to choose
    msg = 'Everyone, choose a path to continue the mission.'
    send_message(msg, update, context)
    for student in group_room_manager.get_full_student_list():
        user_options = path_selection.select_paths_based_on_user(
            student.id, current_task)
        msg = '@' + student.get_telegram_id()
        path_keyboard = create_keyboard_markup(
            path_selection.path_messages(user_options))
        send_message(msg, update, context, reply_markup=path_keyboard)
    # Return to evaluation path response state
    return state.WAIT_FOR_PATH_SEL


def save_path(update: Update, context: CallbackContext):
    """
    This function does save the path a student selects and then either waits for the other players response
    or goes on to wait for the players to be ready for the next task.
    Returns state.WAIT_FOR_USERS_TO_BE_READY if all players chose a path
            state.PATH_SEL otherwise
    """
    # identify the student that send the message
    responding_student = identify_responding_user(update, context)
    response = update.message.text

    # search for matching path and save it to the student
    path_messages = path_selection.create_path_msg_dict()
    for path_id in PathCollection:
        if response == path_messages[path_id.name]:
            responding_student.save_path(Path(path_id))

    if not evaluate_all_path_chosen(update, context):
        # Wait for other users to choose their path
        return state.WAIT_FOR_PATH_SEL
    else:
        # Go to task selection
        return prompt_task_selection(
            update, context,
            get_room_manager_of_group(get_group_chat_id(update)))


def evaluate_all_path_chosen(update: Update, context: CallbackContext):
    """
    Does check if all students already chose a path, if yes resets their path_selected variable
    Returns: True if all student have a path selected
             False otherwise
    """
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))

    for student in group_room_manager.get_full_student_list():
        if not student.path_selected:
            logger.debug("{} path selected = {}".format(
                student.get_name(), student.path_selected))
            return False

    for student in group_room_manager.get_full_student_list():
        student.path_selected = False

    return True


def identify_responding_user(update: Update, context: CallbackContext):
    students = get_room_manager_of_group(
        get_group_chat_id(update)).get_full_student_list()
    for student in students:
        if update.message.from_user.username == student.get_telegram_id():
            return student
