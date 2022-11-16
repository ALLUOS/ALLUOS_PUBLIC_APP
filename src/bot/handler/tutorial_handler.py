from telegram import Update
from telegram.ext import CallbackContext
import logging
import emoji

from . import state
from ..util import create_keyboard_markup, send_message
from ...backend.tools import load_phrases
from ...backend.db.student import get_student

logger = logging.getLogger(__name__)

tutorial_phrases = load_phrases("./data/phrases/tutorial_phrases.json")
tutorial_poll_options = [
    'How to start Escapeling?',
    'How to start an escape mission?',
    'Nevermind, I\'m all set.'
]
# Keyboard for poll options
tutorial_option_keyboard = create_keyboard_markup(tutorial_poll_options, selective=True)


def send_poll(update: Update, context: CallbackContext):
    current_student = get_student(update.effective_user.username)
    msg = tutorial_phrases['poll question'].format(current_student.name)
    send_message(msg, update, context, reply_markup=tutorial_option_keyboard)
    # Return waiting-for-poll-answer state
    return state.TUTORIAL_WAIT_FOR_POLL


def send_tutorial(update: Update, context: CallbackContext):
    if "how to start escapeling" in update.message.text.lower():
        __send_tutorial('escapeling tutorial', update, context)
        return send_poll(update, context)
    if "how to start an escape mission" in update.message.text.lower():
        __send_tutorial('mission tutorial', update, context)
        return send_poll(update, context)
    if "nevermind" in update.message.text.lower():
        msg = emoji.emojize(tutorial_phrases['no question'])
        send_message(msg, update, context, delay=False)
        return state.END

    return state.TUTORIAL_WAIT_FOR_POLL


def __send_tutorial(tutorial_name, update: Update, context: CallbackContext):
    for msg in tutorial_phrases[tutorial_name]:
        if msg.startswith('!IMAGE:'):
            file_name = msg.replace('!IMAGE:', '')
            image_path = f"./data/images/tutorial_images/{file_name}"
            update.message.reply_photo(open(image_path, 'rb'))
        else:
            send_message(msg, update, context, delay=False)
