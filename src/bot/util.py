import random
import time
import json

import emoji
from telegram import (Update, Message, ParseMode,
                      ChatAction, ReplyKeyboardMarkup)

from telegram import error

from telegram.ext import (CallbackContext)

from src.misc.debug_mode import is_debug_mode_active

# Delay range for typing responses in seconds
TYPING_DELAY = [0.75, 1.8]
# maybe increase the value (slower) for actual language learners
READING_DELAY = 0.15

if is_debug_mode_active():
    # value is overwritten for faster messages during development
    READING_DELAY = 0.01


# load the dictionary for Sticker_Ids
id_dict = None
filepath = "./data/sticker/sticker_info.json"
with open(filepath, 'r') as filehandle:
    id_dict = json.load(filehandle)

# load the dictionary of gifs
gif_dict = None
filepath = "./data/gif/gif_info.json"
with open(filepath, 'r') as filehandle:
    gif_dict = json.load(filehandle)


def send_typing_info(update: Update, context: CallbackContext):
    context.bot.send_chat_action(
        chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)


def send_image(image_path, update):
    """
    Sends an image without any description
    """
    try:
        queue("update.message.reply_photo(open("+image_path+", 'rb'), timeout=10000)")
    except FileNotFoundError:
        print("Error: An Image, which the bot was trying to send could not be found, following the Path: "+image_path)


def send_audio(audio_path: str, update: Update, context: CallbackContext):
    """
    Send an audio-file.
    """
    try:
        context.bot.send_audio(
            chat_id=update.effective_message.chat_id,
            audio=open(audio_path, 'rb'))
    except FileNotFoundError:
        print("Error: An Audio-File, which the bot was trying to send could not be found, following the Path: "+audio_path)
        send_message(
            "There seems to be an error with the Audio-File, that I wanted to send you. I am sorry. Please inform us and send us this: "+audio_path)
    print("An audio-file was send:"+audio_path)


def send_message(
        msg: str, update: Update, context: CallbackContext, reply_markup=None,
        text_markup=False, quote=False, delay=True, emojify=True,
        speaker="narrator"):

    if speaker == "harriet":
        msg = ":woman_technologist:" + " " + msg
    if speaker == "elias":
        msg = ":alien:" + " " + msg

    # Sends the message with a random typing delay before
    if delay:
        # Get a random delay
        delay_time = random.uniform(TYPING_DELAY[0], TYPING_DELAY[1])
        # Send chat action to show the bot is typing
        send_typing_info(update, context)
        # Hold execution for the delay
        time.sleep(delay_time)

    # Auto-Emojize messages
    if emojify:
        msg = emoji.emojize(msg)

    # The while loop below trys to send the message, even if the bot is caught in a overflow error.
    did_message_send = False
    while not(did_message_send):
        try:
            # Send the actual message. There are some differences between different-messaging styles.
            if update.message == None:
                context.bot.send_message(
                    chat_id=update.effective_message.chat_id,
                    text=msg, reply_markup=reply_markup)

            elif reply_markup is not None:
                if text_markup:
                    update.message.reply_text(
                        text=msg, quote=quote, reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML)
                else:
                    update.message.reply_text(
                        text=msg, quote=quote, reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML)
            else:
                if text_markup:
                    update.message.reply_text(
                        text=msg, quote=quote, parse_mode=ParseMode.HTML)
                else:
                    if quote:
                        update.message.reply_text(
                            text=msg, quote=quote,
                            parse_mode=ParseMode.HTML)
                    else:
                        context.bot.send_message(
                            chat_id=update.effective_message.chat_id,
                            text=msg,
                            parse_mode=ParseMode.HTML)
            did_message_send = True
        except error.RetryAfter:
            print("This message has not been send, due to the telegram.error.RetryAfter - Problem. Automaticaly retrying after 15 seconds")
            time.sleep(15)

    # reading delay
    if delay:
        delay_time = len(msg.split(' ')) * READING_DELAY
        time.sleep(delay_time)


def send_animation(
        gif_link: str, update: Update, context: CallbackContext,
        reply_markup=None, quote=False, delay=False):
    """
    Sends out an Animation. Therefore a Link/Path to the GIF must be provided.
    """
    if delay:
        # Send a typing chat action for a random delay time
        delay_time = random.uniform(TYPING_DELAY[0], TYPING_DELAY[1])
        send_typing_info(update, context)
        time.sleep(delay_time)

    update.message.reply_animation(
        gif_link, reply_markup=reply_markup, quote=quote)


def get_gif_link(gif_type: str) -> str:
    """
    Returns a random gif URL depending on the type on gif that is needed

    Args:
    gif_type (str): ["correct", "wrong", "motivation", "lets_talk",
                    "think", "fix_it", "earth"]
    """

    gif_link = random.choice(gif_dict[gif_type])

    return gif_link


def send_image(update, image_path):
    """
    Sends an image without any description
    """
    update.message.reply_photo(
        open(image_path, 'rb'),
        timeout=10000, quote=False)


def get_sticker_id(sticker_name: str) -> str:
    """
    Returns a the id of the sticker, which can be found in the sticker_info.json
    """

    id = id_dict[sticker_name]

    return id


def send_sticker(update, stickerid: str):
    """
    Sends an sticker
    """
    update.message.reply_sticker(stickerid, timeout=10000, quote=False)


def get_group_chat_id(update: Update) -> str:
    """
    Gets the chat id of a group from the update.

    Args:
        The update from which to retrieve the chat id.

    Returns:
        The chat id of the group.
    """
    return _get_group_chat_id(str(update.effective_chat.id))


def get_group_chat_id_from_message(message: Message) -> str:
    """
    Gets the chat id of a group from a message.

    Args:
        The message from which to retrieve the chat id.

    Returns:
        The chat id of the group.
    """
    return _get_group_chat_id(str(message.chat.id))


def _get_group_chat_id(chat_id: str) -> str:
    """
    Removes the identification for a group from the chat id.
    """
    if chat_id.startswith('-100'):
        chat_id = chat_id[4:]
    return chat_id


def create_keyboard_markup(
        options: list, selective=True) -> ReplyKeyboardMarkup:
    """
    Create a reply keyboard markup with the given options to show to the user.

    Args:
        options (list): A list of options as strings that should be shown to the user.

    Returns:
        The created reply keyboard.
    """
    options_keyboard = [[option] for option in options]
    return ReplyKeyboardMarkup(
        keyboard=options_keyboard, resize_keyboard=True, one_time_keyboard=True,
        selective=selective)


def transform_codeword_to_emoji(code: str) -> str:
    number_to_emoji = {
        1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣",
        7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 0: "0️⃣"}
    emoji_code = ""
    for number in code:
        emoji_code += " "+number_to_emoji[int(number)]
    return emoji_code
