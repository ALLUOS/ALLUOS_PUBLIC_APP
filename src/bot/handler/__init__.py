from telegram.ext import (CommandHandler, MessageHandler,
                          Filters, ConversationHandler, CallbackQueryHandler)
import re

from . import state
from . import private_base
from . import room_handler as room
from . import tutorial_handler as tutorial
from . import faq_handler as faq
from .task import sen_corr_handler as sen_corr
from .task import vocab_desc_handler as vocab_desc
from .task import discussion_handler as discuss
from .task import listening_task_handler as listening_task_handler
from ...backend.adaptability.path_selection import path_messages, get_all_paths
from ..filters.text_list import TextList


"""
Create the sentence correction conversation handler
"""
# Create filters for sentence correction task
filter_correct = TextList(['Correct'], case_sensitive=False)
filter_incorrect = TextList(['Incorrect'], case_sensitive=False)
filter_sen_corr = TextList(["sentence correction"], case_sensitive=False)

sentence_corr_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filter_sen_corr, sen_corr.task_selection)
    ],
    states={
        state.SEN_CORR_WAIT_FOR_ANSWER_SENTENCE: [
            MessageHandler(filter_correct & (~ Filters.command),
                           sen_corr.task_response_correct),
            MessageHandler(filter_incorrect & (~ Filters.command),
                           sen_corr.task_response_incorrect)
        ],
        state.SEN_CORR_WAIT_FOR_ANSWER_IDENTIFICATION: [
            MessageHandler(Filters.text & (~ Filters.command),
                           sen_corr.evaluate_sentence_mistake_identification)
        ],
        state.SEN_CORR_WAIT_FOR_ANSWER_CORRECTION: [
            MessageHandler(Filters.text & (~ Filters.command),
                           sen_corr.evaluate_sentence_mistake_correction)
        ]
    },
    fallbacks=[
        CommandHandler('stop', sen_corr.stop_task,
                       filters=Filters.chat_type.groups)
    ],
    map_to_parent={
        state.SEN_CORR_END_SUCCESS: state.WAIT_FOR_PASSCODE,
        state.SEN_CORR_SEL_WRONG_USER: state.WAIT_FOR_TASK_SELECTION,
        state.SEN_CORR_END_FAIL: state.WAIT_FOR_RESTART_POLL,
        state.SEN_CORR_STOP: state.END,
        state.WAIT_FOR_TASK_SELECTION: state.WAIT_FOR_TASK_SELECTION
    },
    per_user=False
)


"""
Create the vocabulary guessing conversation handler
"""
# Create filter for vocabulary guessing task
filter_vocab_guessing = TextList(["vocabulary guessing"], case_sensitive=False)

vocab_desc_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filter_vocab_guessing,
                       vocab_desc.task_selection, pass_job_queue=True)
    ],
    states={
        state.VOCAB_DESC_WAIT_FOR_GUESS: [
            MessageHandler(Filters.text & (~ Filters.command),
                           vocab_desc.check_for_guess)
        ]
    },
    fallbacks=[
        CommandHandler('stop', vocab_desc.stop_task,
                       filters=Filters.chat_type.groups)
    ],

    map_to_parent={
        state.VOCAB_DESC_END_SUCCESS: state.WAIT_FOR_PASSCODE,
        state.VOCAB_DESC_SEL_WRONG_USER: state.WAIT_FOR_TASK_SELECTION,
        state.VOCAB_DESC_END_FAIL: state.WAIT_FOR_RESTART_POLL,
        state.VOCAB_DESC_STOP: state.END,
        state.WAIT_FOR_TASK_SELECTION: state.WAIT_FOR_TASK_SELECTION
    },
    per_user=False
)


"""
Create the discussion task conversation handler
"""
filter_discussion = TextList(["discussion"], case_sensitive=False)
discussion_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filter_discussion,
                       discuss.task_selection, pass_job_queue=True)
    ],
    states={
        state.DISCUSS_Q1: [
            MessageHandler(None, discuss.handle_q1)
        ],
        state.DISCUSS_Q2: [
            MessageHandler(None, discuss.handle_q2)
        ],
        state.DISCUSS_Q3: [
            MessageHandler(None, discuss.handle_q3)
        ]
    },
    fallbacks=[
        CommandHandler('stop', discuss.stop_task,
                       filters=Filters.chat_type.groups)
    ],
    map_to_parent={
        state.DISCUSS_END_SUCCESS: state.WAIT_FOR_PASSCODE,
        state.DISCUSS_SEL_WRONG_USER: state.WAIT_FOR_TASK_SELECTION,
        state.DISCUSS_END_FAIL: state.WAIT_FOR_RESTART_POLL,
        state.DISCUSS_STOP: state.END,
        state.WAIT_FOR_TASK_SELECTION: state.WAIT_FOR_TASK_SELECTION
    },
    per_user=False
)


"""
Create the listening task conversation handler
"""
filter_listening = TextList(["listening"], case_sensitive=False)
filter_extension = TextList(["Yes", "No"], case_sensitive=False)
listen_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filter_listening,
                       listening_task_handler.task_selection, pass_job_queue=True)

    ],
    states={
        state.DISCUSSION_TIME: [
            MessageHandler(None, listening_task_handler.evaluate_answer, pass_job_queue=True),
            CallbackQueryHandler(listening_task_handler.answer_early_button, pass_job_queue=True)
        ],
    },
    fallbacks=[
        CommandHandler('stop', listening_task_handler.stop_task,
                       filters=Filters.chat_type.groups)
    ],
    map_to_parent={
        state.LISTENING_SEL_WRONG_USER: state.WAIT_FOR_TASK_SELECTION,
        state.LISTENING_STOP: state.END,
        state.WAIT_FOR_TASK_SELECTION: state.WAIT_FOR_TASK_SELECTION
    },
    per_user=False
)


"""
Create tutorial conversation handler
"""
filter_poll = TextList(['How to start Escapeling?',
                        'How to start an escape mission?',
                        'Nevermind, I\'m all set.'], case_sensitive=False)

tutorial_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('tutorial', tutorial.send_poll)
    ],
    states={
        state.TUTORIAL_WAIT_FOR_POLL: [
            MessageHandler(filter_poll, tutorial.send_tutorial),
        ]
    },
    fallbacks=[
        CommandHandler('stop', room.stop_group, filters=Filters.chat_type.groups),
        CommandHandler('stop', private_base.stop, filters=Filters.chat_type.private)
    ],
    per_user=False
)


"""
Create FAQ conversation handler.
Please note: if you want to change the question-answer pairs offered by the FAQ, please make adjustments in 
"data/phrases/faq_questions.json". You do not need to change any code.
"""
filter_questions = TextList(list(faq.q_a_pairs.keys()), case_sensitive=False)
filter_confirmation = TextList(
    faq.confirmation_prompt_answers, case_sensitive=False)

faq_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('faq', faq.send_poll)
    ],
    states={
        state.FAQ_WAIT_FOR_POLL: [
            MessageHandler(filter_questions, faq.send_answer),
            MessageHandler(filter_confirmation, faq.handle_follow_ups)
        ]
    },
    fallbacks=[
        CommandHandler('stop', room.stop_group, filters=Filters.chat_type.groups),
        CommandHandler('stop', private_base.stop, filters=Filters.chat_type.private)
    ],
    per_user=False
)


"""
Create the room conversation handler
"""
filter_restart = TextList(['Yes', 'No'])
filter_tasks = TextList(
    ['Vocabulary Guessing', 'Sentence Correction', 'Discussion', 'Listening'],
    case_sensitive=False)
filter_paths = TextList(path_messages(get_all_paths()), case_sensitive=False)

room_manager_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', room.start_escape,
                       filters=Filters.chat_type.groups),
        CommandHandler('debug', room.debug,
                       filters=Filters.chat_type.groups)
    ],
    states={
        state.WAIT_FOR_USERS_TO_BE_READY: [
            MessageHandler(Filters.regex(re.compile(
                r'yes', re.IGNORECASE)), room.evaluate_readiness),
            CallbackQueryHandler(room.button_manager, pass_job_queue=True)
        ],
        state.WAIT_FOR_PATH_SEL: [
            MessageHandler(filter_paths, room.save_path)
        ],
        state.WAIT_FOR_TASK_SELECTION: [
            sentence_corr_conv_handler,
            vocab_desc_conv_handler,
            discussion_conv_handler,
            listen_conv_handler
        ],
        state.WAIT_FOR_PASSCODE: [
            MessageHandler(None, room.check_passcode)
        ],
        state.WAIT_FOR_RESTART_POLL: [
            MessageHandler(filter_restart, room.evaluate_restart),
        ]
    },
    fallbacks=[
        CommandHandler('stop', room.stop_group,
                       filters=Filters.chat_type.groups)
    ],
    per_user=False
)


"""
Create the conversation handler for the private chat
"""
private_base_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', private_base.start,
                       filters=Filters.chat_type.private)
    ],
    states={
        state.WFI_USER_NAME: [
            MessageHandler(Filters.text & (~ Filters.command), private_base._save_student)
        ],
        state.WFD_FLASHBACK: [
            MessageHandler(Filters.regex(re.compile(
                r'shadow', re.IGNORECASE)), private_base.send_story_shadow),
            MessageHandler(Filters.regex(re.compile(
                r'light', re.IGNORECASE)), private_base.send_story_light),
            MessageHandler(Filters.regex(re.compile(
                r'voices', re.IGNORECASE)), private_base.send_story_voices)
        ],
        state.WFD_CREATE_OR_JOIN_GROUP_OR_SEE_ACHIEVEMENTS: [
            MessageHandler(Filters.regex(re.compile(
                r'create', re.IGNORECASE)), private_base.create_group_and_send_code),
            MessageHandler(Filters.regex(re.compile(
                r'join', re.IGNORECASE)), private_base.ask_for_registration_code),
            MessageHandler(Filters.regex(re.compile(
                r'achievements', re.IGNORECASE)), private_base.send_achievements)
        ],
        state.WFI_REGISTRATION_CODE: [
            MessageHandler(Filters.text, private_base.join_group)
        ],
        state.WFD_CODE_OR_CANCEL: [
            MessageHandler(Filters.regex(re.compile(
                r'try', re.IGNORECASE)), private_base.ask_for_registration_code),
            MessageHandler(Filters.regex(re.compile(
                r'cancel', re.IGNORECASE)), private_base.say_goodbye)
        ],
        state.WFD_SET_USER_NAME: [
            MessageHandler(Filters.regex(re.compile(
                r'help', re.IGNORECASE)), private_base.show_username_help),
            MessageHandler(Filters.regex(re.compile(
                r'set a username', re.IGNORECASE)), private_base.check_username),
            MessageHandler(Filters.regex(re.compile(
                r'cancel', re.IGNORECASE)), private_base.say_goodbye)
        ],
        state.WFD_PRIVACY_SETTINGS: [
            MessageHandler(Filters.regex(re.compile(
                r'i added you as an contact', re.IGNORECASE)), private_base.create_group_and_send_code),
            MessageHandler(Filters.regex(re.compile(r'i changed my privacy settings',
                           re.IGNORECASE)), private_base.create_group_and_send_code),
            MessageHandler(Filters.regex(re.compile(
                r'cancel', re.IGNORECASE)), private_base.say_goodbye)
        ]
    },
    fallbacks=[
        CommandHandler('stop', private_base.stop,
                       filters=Filters.chat_type.private)
    ]
)
