from telegram import Update
from telegram.ext import CallbackContext
import logging
import emoji

from . import state
from ..util import create_keyboard_markup, send_message
from ...backend.tools import load_phrases

logger = logging.getLogger(__name__)
q_a_pairs = load_phrases("./data/phrases/faq_questions.json")
confirmation_prompt_answers = ["Yes, I want to ask another question.",
                               "No thanks, I'm good for now."]

# Keyboard for poll options
faq_option_keyboard = create_keyboard_markup(list(q_a_pairs.keys()), selective=True)
confirmation_keyboard = create_keyboard_markup(confirmation_prompt_answers, selective=True)

def send_poll(update: Update, context: CallbackContext):
    msg = 'What is your question?'
    # TODO: make sure that only the person asking for FAQ stuff gets the keyboard prompt
    send_message(msg, update, context, reply_markup=faq_option_keyboard)
    # Return waiting for poll answer state 
    return state.FAQ_WAIT_FOR_POLL

def handle_follow_ups(update:Update, context: CallbackContext):
    if "yes" in update.message.text.lower():
        return send_poll(update, context)
    else:
        msg = emoji.emojize("Okay, let's get back to the game then! :smiling_face_with_smiling_eyes:")
        send_message(msg, update, context, quote=True)
        return state.END

def send_answer(update: Update, context: CallbackContext):
    try:
        msg = q_a_pairs[update.message.text]
    except:
        msg = "Oh! I seem to be having some problems retrieving the answer to your question right now. Plese refer to" \
              " our website FAQ to find the answer you were looking for.\nhttps://alluos.github.io/2020/03/03/FAQ.html"
    send_message(msg, update, context, quote=True)
    send_message("Do you have any more questions?", update, context, reply_markup=confirmation_keyboard)
    return state.FAQ_WAIT_FOR_POLL
