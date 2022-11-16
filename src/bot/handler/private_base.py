from telegram import (Update, ReplyKeyboardMarkup)
from telegram.ext import (CallbackContext)
from telethon.errors.rpcerrorlist import UserPrivacyRestrictedError
import emoji
import numpy as np
import logging
import time
import re

from . import state
from ...backend.db.student import get_student, create_student
from ...backend.db.group import create_group, add_student_to_group
from ..util import send_message, send_image, get_gif_link, send_animation, get_sticker_id, send_sticker

intro_video_id = "BAACAgIAAxkDAAIKqmAIbdPwstqafBRqbFPl0xC7ydQvAAJlDQAC_1ZBSCXYFLAMD5TRHgQ"
intro_video_link = "https://youtu.be/GBRieHAuEao"
logger = logging.getLogger(__name__)
group_admin_phone_number = None


def _send_image(update, image_path):
    """
    Sends an image without any description
    """
    update.message.reply_photo(open(image_path, 'rb'), timeout=10000)


def _send_image_by_id(update, image_id):
    """
    Sends an image without any description
    """
    update.message.reply_photo(image_id)


def _send_video(update, video_path):
    """
    Sends a video without any description
    """
    update.message.reply_video(open(video_path, 'rb'), timeout=10000)


def _send_video_by_id(update, video_id):
    """
    Sends a video without any description
    """
    update.message.reply_video(video_id)


def set_phone_number(phone_number: str):
    """
    Sets the phone number of the group admin
    """
    global group_admin_phone_number
    group_admin_phone_number = phone_number


def start(update: Update, context: CallbackContext):
    """
    Greets the student and checks whether they already exist.
    If the student does not exist, they will be asked for their name.
    Otherwise the student is asked whether he wants to join or create a group
    """
    return_state = None
    username = update.effective_user.username
    current_student = get_student(username)
    if current_student:
        greeting = _get_greeting(current_student.name)
        send_message(greeting, update, context)
        return_state = _choose_join_or_create_group_or_display_achievements_action(
            update, context)
    else:
        # send short instruction on how to use the bot.
        send_image(
            update, "./data/images/tutorial_images/where_are_my_options.png")
        send_message(
            "If you can not find the answering-options, you may have to press the button in the red circle.",
            update, context)
        # Send intro to story
        send_message(
            "You wake up and find yourself in a strange and unfamiliar place. You’re not sure how you got here or what happened.",
            update, context)
        buttons = [
            ['A huge shadow coming from the sky'],
            ['A bright flash of light'],
            ['Voices speaking in a language you don\'t understand']]
        markup_select_action = ReplyKeyboardMarkup(
            buttons, resize_keyboard=True, one_time_keyboard=True)
        send_message("What is the last thing you remember?",
                     update, context, reply_markup=markup_select_action)
        return_state = state.WFD_FLASHBACK
    return return_state


def _get_greeting(name: str = ''):
    """
    Creates a greeting.
    Args:
        name (str): The persons name to greet.
    Returns:
        A greeting.
    """
    begins = ['Hello', 'Hi', 'Hey']
    unknown_names = ['unknown', 'stranger']
    name_to_use = name if name else np.random.choice(unknown_names, 1)[0]
    begin = np.random.choice(begins, 1)[0]
    emoji_end = ':grinning_face_with_smiling_eyes:'
    return emoji.emojize('{} {} {}'.format(begin, name_to_use, emoji_end))


def _choose_join_or_create_group_or_display_achievements_action(
        update: Update, context: CallbackContext):
    """
    Asks the student whether they want to do join or create a group.
    """
    buttons = [
        ['Join a group 🧍🏾‍♂️🧍🏻🧍🏼‍♀️'],
        ['Create a group ✨'],
        ['See achievements 🎖️']]
    markup_select_action = ReplyKeyboardMarkup(
        buttons, resize_keyboard=True, one_time_keyboard=True)
    select_action_message = "What do you want to do?"
    send_message(select_action_message, update, context,
                 reply_markup=markup_select_action)
    return state.WFD_CREATE_OR_JOIN_GROUP_OR_SEE_ACHIEVEMENTS


def _ask_for_name(update: Update, context: CallbackContext) -> int:
    """
    Asks the student for their name.
    """
    message = 'If you want to work together, you will need to let the other humans know your name. Please type in your name.'
    send_message(message, update, context)
    return state.WFI_USER_NAME


def _save_student(update: Update, context: CallbackContext):
    """
    Saves the student to the database and sends info.
    """
    return_state = None
    # First, save the name to our context
    name = update.message.text.strip()
    context.user_data[state.USERS_NAME] = name
    # Then, check if the users has a telegram username
    username = update.effective_user.username
    if username is None:
        return_state = _ask_user_to_set_a_username(update, context)
    else:
        create_student(username, name)
        message = 'Okay {}, you have introduced yourself to the other humans. You will soon start to work together on the first task that will bring you closer to freedom.'.format(
            context.user_data[state.USERS_NAME])
        send_message(message, update, context)
        return_state = _choose_join_or_create_group_or_display_achievements_action(
            update, context)
    return return_state


def _ask_user_to_set_a_username(update: Update, context: CallbackContext):
    """
    Asks the user to set a username.
    """
    message = 'To ensure that the application works properly, you must enter a username in telegram. If you need help with this, please let me know. While you give yourself a username, I will be waiting.'
    buttons = [['I need help.'], ['I have set a username.'], ['Cancel']]
    markup = ReplyKeyboardMarkup(
        buttons, resize_keyboard=True, one_time_keyboard=True)
    send_message(message, update, context, reply_markup=markup)
    return state.WFD_SET_USER_NAME


def send_story_shadow(update: Update, context: CallbackContext):
    """
    Sends some story information if the user has selected that he has seen a shadow
    """
    _send_image(update, "./data/images/shadow.jpeg")
    return _send_story_intro(update, context)


def send_story_light(update: Update, context: CallbackContext):
    """
    Sends some story information if the user has selected that he has seen a light
    """
    _send_image(update, "./data/images/light.jpeg")
    return _send_story_intro(update, context)


def send_story_voices(update: Update, context: CallbackContext):
    """
    Sends some story information if the user has selected that he has heards voices
    """
    _send_image(update, "./data/images/voices.jpeg")
    return _send_story_intro(update, context)


def _send_story_intro(update: Update, context: CallbackContext):
    """
    Sends a message and the video explaining the intro to our story, then refers to asking the username
    """
    message = "You start to remember what happened. You are on a spaceship."
    send_message(message, update, context)

    # send rocket emoji
    id = get_sticker_id("rocket")
    send_sticker(update, id)

    message = "How did you get here? Did someone kidnap you and bring you here? And why did they choose you?"
    send_message(message, update, context)

    # _send_video_by_id(update, intro_video_id) Send video link istead
    send_message(intro_video_link, update, context)
    return _ask_for_name(update, context)


def show_username_help(update: Update, context: CallbackContext):
    """
    Shows the users the help for setting the username.
    """
    message = 'You can find information about the username in telegram and how to set it here: https://telegram.org/faq#usernames-and-t-me.'
    buttons = [['I have set a username.'], ['Cancel']]
    markup = ReplyKeyboardMarkup(
        buttons, resize_keyboard=True, one_time_keyboard=True)
    send_message(message, update, context, reply_markup=markup)
    return state.WFD_SET_USER_NAME


def check_username(update: Update, context: CallbackContext):
    """
    Checks whether the user has set a username or not.
    """
    return_state = None
    username = update.effective_user.username
    if username is None:
        message = 'You still have not assigned a username. Please enter a username in your telegram account settings.'
        send_message(message, update, context)
        return_state = _ask_user_to_set_a_username(update, context)
    else:
        create_student(username, context.user_data[state.USERS_NAME])
        message = 'Okay {}, you have introduced yourself to the other humans. You will soon start to work together on the first task that will bring you closer to freedom.'.format(
            context.user_data[state.USERS_NAME])
        send_message(message, update, context)
        return_state = _choose_join_or_create_group_or_display_achievements_action(
            update, context)
    return return_state


def create_group_and_send_code(update: Update, context: CallbackContext):
    """
    Creates the group in the database and telegram and adds the user to it.
    Afterwards the registration code is send to the user.
    """
    return_state = None
    telegram_user_id = update.effective_user.username
    try:
        result = create_group(telegram_user_id)
        if result.successful:
            message = 'I created a new group. While playing in a Group this private Chat stays inactive. You can only play in one group at a time. To invite your fellow students to your Group send them the following registration code:'
            send_message(message, update, context)
            update.message.reply_text('{}'.format(result.message))
            return _end_group_assignment(update, context)
        else:
            message = 'Sorry I was not able to create a new group for you. Please try it later again. Goodbye.'
            update.message.reply_text(message)
            return_state = state.END
    except UserPrivacyRestrictedError:
        # The user cannot be added to the group because their privacy settings do not allow it.
        message = 'I tried to add you to the group, but your privacy settings do not allow me to add you. In order to allow me to add you, you can either add this number ({}) as a contact or change your privacy settings for groups and channels.'.format(
            group_admin_phone_number)
        buttons = [['I added you as an contact.'], [
            'I changed my privacy settings.'], ['Cancel']]
        markup = ReplyKeyboardMarkup(
            buttons, resize_keyboard=True, one_time_keyboard=True)
        send_message(message, update, context, reply_markup=markup)
        return_state = state.WFD_PRIVACY_SETTINGS
    return return_state


def ask_for_registration_code(update: Update, context: CallbackContext):
    """
    Asks the user to enter the registration code.
    """
    message = 'Please enter the registration code.'
    send_message(message, update, context)
    return state.WFI_REGISTRATION_CODE


def choose_achievement_image(completed_achievements_str: str):
    """
    chooses between the different images representing the Ranks
    """
    path = "./data/images/uniforms/recruit_blue.png"
    if re.search(r"Fleet Admiral", completed_achievements_str):
        path = "./data/images/uniforms/admiral_white.png"
        return path
    if re.search(r"Admiral", completed_achievements_str):
        path = "./data/images/uniforms/admiral_blue.png"
    if re.search(r"Vice Admiral", completed_achievements_str):
        path = "./data/images/uniforms/vice_admiral_blue.png"
    if re.search(r"Captain", completed_achievements_str):
        path = "./data/images/uniforms/captain_blue.png"
    if re.search(r"Commander", completed_achievements_str):
        path = "./data/images/uniforms/commander_blue.png"
    if re.search(r"Lieutenant-Commander", completed_achievements_str):
        path = "./data/images/uniforms/lieutenant_commander_blue.png"
        return path
    if re.search(r"Lieutenant", completed_achievements_str):
        path = "./data/images/uniforms/lieutenant_blue.png"
    if re.search(r"Junior Lieutenant", completed_achievements_str):
        path = "./data/images/uniforms/junior_lieutenant_blue.png"
    if re.search(r"Commodore", completed_achievements_str):
        path = "./data/images/uniforms/commodore_blue.png"
    if re.search(r"Cadet", completed_achievements_str):
        path = "./data/images/uniforms/cadett_blue.png"

    return path


def send_achievements(update: Update, context: CallbackContext):
    """
    Displays all completed and remaining achievements to the user.
    """
    # Get student to display achievements to
    username = update.effective_user.username
    current_student = get_student(username)

    # Get list of completed achievements
    completed_achievements = current_student.get_completed_achievements()
    # Check if there are any
    if len(completed_achievements) > 0:
        # Convert list to string if there is at least one element in it and display it to the user
        completed_achievements_str = _convert_achievement_list_to_str(
            current_student.get_completed_achievements())
        update.message.reply_text(
            text='You completed the following achievements:\n{}'.format(
                completed_achievements_str),
            quote=False)
        img_path = choose_achievement_image(completed_achievements_str)
        send_image(update, img_path)
    else:
        # Inform user that there are none
        update.message.reply_text(
            text='You have not yet completed an achievement. Keep going!',
            quote=False)
        send_image(update, "./data/images/uniforms/recruit_blue.png")

    # Show open achievements in similar fashion
    open_achievements = current_student.get_next_open_achievements()
    if len(open_achievements) > 0:
        open_achievements_str = _convert_achievement_list_to_str(
            open_achievements)
        update.message.reply_text(
            text='The following achievements are still open:\n{}'.format(
                open_achievements_str),
            quote=False)
    else:
        update.message.reply_text(
            text='Congratulations, you have earned all achievements!',
            quote=False)

    # Return back to letting the user choose an option
    return _choose_join_or_create_group_or_display_achievements_action(
        update, context)


def _convert_achievement_list_to_str(achievements):
    """
    Converts a list of achievement objects to a single string that can be sent to students via Telegram
    """
    return '\n'.join(map(str, achievements))


def join_group(update: Update, context: CallbackContext):
    """
    Adds the user to the group.
    """
    return_state = None
    result = add_student_to_group(
        update.message.text, update.effective_user.username)
    if result.successful:
        message = 'You can only play in one group at a time. This private chat is inactive while you play. Use the following link to join the group: {}'.format(
            result.message)
        send_message(message, update, context)
        return _end_group_assignment(update, context)
    else:
        update.message.reply_text(text=result.message)
        message = 'Do you want to try another code or do you want to cancel?'
        buttons = [['Try another code'], ['Cancel']]
        markup_select_action = ReplyKeyboardMarkup(
            buttons, resize_keyboard=True, one_time_keyboard=True)
        send_message(message, update, context,
                     reply_markup=markup_select_action)
        return_state = state.WFD_CODE_OR_CANCEL
    return return_state


def _end_group_assignment(update: Update, context: CallbackContext):
    """
    Informs the user that group assignment has worked.
    """
    message = emoji.emojize(
        'You have a team. You know your mission. Everything is ready. Time to start your adventure. Good luck! :four_leaf_clover:')
    send_message(message, update, context)
    return state.END


def say_goodbye(update: Update, context: CallbackContext):
    """
    Finishes the conversation.
    """
    message = 'See you next time. Bye :)'
    send_message(message, update, context)
    return state.END


def stop(update: Update, context: CallbackContext):
    """
    Dummy stop method for private chats.
    """
    message = 'Goodbye. To start me again write /start.'
    send_message(message, update, context)
    return state.END
