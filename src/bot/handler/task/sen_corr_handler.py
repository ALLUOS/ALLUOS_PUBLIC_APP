from telegram import (Update, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (
    CommandHandler, MessageHandler, Filters, ConversationHandler,
    CallbackContext)
import logging
import json

from ..room_handler import end_task_group, get_room_manager_of_group, remove_room_manager_of_group
from .. import state
from ....backend.tasks.sentence_correction_storage import get_sentence_correction_task_of_group, remove_sentence_correction_task_of_group
from ...util import get_gif_link, get_group_chat_id, send_animation, send_message, create_keyboard_markup
from ....backend.db.task import insert_sentence_correction_adaptive_data_entry


logger = logging.getLogger(__name__)


remove_keyboard_markup = ReplyKeyboardRemove()
keyboard_bool = create_keyboard_markup(['Correct', 'Incorrect'])


def task_selection(update: Update, context: CallbackContext):
    """
    Evaluates task selection messages.
    If the sentence correction-task was requested by the right user,
    show the task-description, otherwise return to the task selection
    """
    # Get room manager
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    # Get selected user who has to chose the task
    selected_usr = group_room_manager.get_selected_user()
    # Check if the message is from the selected user
    if update.message.from_user.username == selected_usr:
        # Set task in room manager
        group_room_manager.next_task("sentence correction")
        return show_sentence_task_description(update, context)
    else:
        # Wait for message from the correct user -> go back to task selection
        return state.SEN_CORR_SEL_WRONG_USER


def show_sentence_task_description(update: Update, context: CallbackContext):
    group_chat_id = get_group_chat_id(update)
    sentence_task = get_sentence_correction_task_of_group(group_chat_id)
    send_message(sentence_task.get_task_instructions(),
                 update, context, text_markup=True)

    gif_url = get_gif_link("fix_it")
    send_animation(gif_url, update, context)

    return present_first_task_iteration(update, context)


def send_sentence(update: Update, context: CallbackContext):
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    # Send sentence to all students and add custom response keyboard for selected user
    send_message(sentence_task.get_sentence_msg() + "\n" + sentence_task.get_user_selected_msg(),
                 update, context, reply_markup=keyboard_bool, text_markup=True)


def present_first_task_iteration(update: Update, context: CallbackContext):
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    # Log info about proficiency
    logger.info('Test information: Start of sentence correction task')
    sentence_task.log_proficiencies()
    # Initialize iteration
    sentence_task.next_group_iteration()
    # Send info about first iteration
    send_message(sentence_task.get_first_iteration_info_msg(), update, context)
    # Randomly select a user
    sentence_task.select_next_user()
    # Send sentence to all students
    send_sentence(update, context)
    return state.SEN_CORR_WAIT_FOR_ANSWER_SENTENCE


def present_next_task_iteration(update: Update, context: CallbackContext):
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))

    # Get adaptive data.
    sentence_adaptive_data_entry = sentence_task.get_adaptive_data_entry(
        get_group_chat_id(
            update))
    # Insert db entry.
    insert_sentence_correction_adaptive_data_entry(sentence_adaptive_data_entry)

    # Check if group iteration is finished
    if sentence_task.is_group_iteration_finished():
        # Check if all responses were correct:
        if sentence_task.is_correct_group_iteration():
            # Combine positive feedback and code + Recap of current codeword
            send_message(
                sentence_task.get_correct_group_iter_feedback() + "\n" +
                sentence_task.get_codeword_recap(),
                update, context)
            # Increment counter
            sentence_task.increment_correct_group_iteration()

        else:
            # Feedback
            send_message(
                sentence_task.get_incorrect_group_iter_feedback(),
                update, context)
            # Increment counter
            sentence_task.increment_incorrect_group_iteration()

        # Reset everything in the iteration over the group
        sentence_task.next_group_iteration()

    # Check if task is finished
    if sentence_task.is_finished():
        # Get room manager for global tracking of repeatability
        group_room_manager = get_room_manager_of_group(
            get_group_chat_id(update))
        # increment repetitions counter
        group_room_manager.increment_task_rep_count("sentence correction")
        # check if task can be repeated, i.e. check if the task repetition counter is less than 2
        if not sentence_task.is_success():
            if group_room_manager._reps_counter["sentence correction"] < 2:
                # add task back to list of available tasks
                group_room_manager.repeat_current_task("sentence correction")
        # End the task and go back to room manager
        return end_task(
            update, context, success=sentence_task.is_success(),
            codeword=sentence_task.get_codeword())
    # Log info about proficiency
    else:
        logger.info('Test information: Next sentence')
        sentence_task.log_proficiencies()
        # Send info about next iteration
        update.message.reply_text(
            text=sentence_task.get_next_iteration_info_msg(),
            quote=False)
        # Randomly select a user
        sentence_task.select_next_user()
        send_sentence(update, context)
        return state.SEN_CORR_WAIT_FOR_ANSWER_SENTENCE


def task_response_correct(update: Update, context: CallbackContext):
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    # First check if message was sent from the selected user
    if not check_selected_user(update):
        # Update adaptive data counter.
        sentence_task.n_messages_non_selected_users += 1
        return state.SEN_CORR_WAIT_FOR_ANSWER_SENTENCE

    # Update adaptive data counter.
    sentence_task.n_messages_selected_user += 1
    # User says sentence was correct via the reply keyboard
    return _task_response(update, context, True)


def task_response_incorrect(update: Update, context: CallbackContext):
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    # First check if message was sent from the selected user
    if not check_selected_user(update):
        # Update adaptive data counter.
        sentence_task.n_messages_non_selected_users += 1
        return state.SEN_CORR_WAIT_FOR_ANSWER_SENTENCE

    # Update adaptive data counter.
    sentence_task.n_messages_selected_user += 1
    # User says sentence was incorrect via the reply keyboard
    return _task_response(update, context, False)


def _task_response(update: Update, context: CallbackContext, response: bool):

    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    # Get the truth about the sentence
    truth_answer = sentence_task.get_current_sentence_truth()
    # Different cases according to task flow

    if truth_answer == True and response == True:

        # Log user answer
        logger.info('Test information: User response = {}'.format(
            "Sentence is correct"))

        # Correct sentence and answer also correct -> Go to next user
        sentence_task.increment_correct_count()
        send_message(sentence_task.get_correct_response_feedback(),
                     update, context, reply_markup=remove_keyboard_markup)

        # Update proficiencies and go to next task
        sentence_task.update_proficiencies(correct=True)
        return present_next_task_iteration(update, context)

    if truth_answer == True and response == False:
        # Log user answer
        logger.info(
            'Test information: User response = {}'.format(
                "Sentence is incorrect"))
        # Correct sentence but incorrect answer
        send_message(sentence_task.get_feedback_no_error(), update,
                     context, reply_markup=remove_keyboard_markup)
        # Update proficiencies and go to next task
        sentence_task.update_proficiencies(correct=False)
        return present_next_task_iteration(update, context)

    if truth_answer == False and response == True:

        # Log user answer
        logger.info('Test information: User response = {}'.format(
            "Sentence is correct"))

        # Incorrect sentence not identified
        send_message(sentence_task.get_feedback_missed_error(),
                     update, context, reply_markup=remove_keyboard_markup)

        sentence_sub_types = sentence_task.curr_sentence.sub_types

        # Adaptibility: display appropriate grammar hint
        send_grammar_feedback(update, context, sentence_sub_types, "hint")

        return _identify_sentence_mistake(update, context)

    if truth_answer == False and response == False:
        # Log user answer
        logger.info(
            'Test information: User response = {}'.format(
                "Sentence is incorrect"))
        # Incorrect sentence correctly identified
        send_message(sentence_task.get_correct_response_feedback(),
                     update, context, reply_markup=remove_keyboard_markup)
        return _identify_sentence_mistake(update, context)


def send_grammar_feedback(
        update: Update, context: CallbackContext, sentence_sub_types: list,
        hint_type: str):
    """Send message with a grammar tip that is shown when user
    assume sentence is correct when it's wrong.
    Used in Sentence Correction task.

    Args:
    sentence_sub_types -- sub types as list
    hint_type -- "hint" or "grammar_rule" - specifying the output type for the user
    """
    # Log which sub_type user was not able to identify as wrong
    logger.info(f"Wrong sentence of subtype {sentence_sub_types}"
                " marked as correct by user.")

    # Add the subtype to tracker of already presented grammar rules
    group_chat_id = get_group_chat_id(update)
    sentence_task = get_sentence_correction_task_of_group(group_chat_id)

    if hint_type == "grammar_rule":
        sentence_task.grammar_rules_used.append(sentence_sub_types)

    # Retrieve appropriate feedback and send it as Telegram message
    feedback = get_grammar_tip(sentence_sub_types, hint_type)
    send_message(feedback, update, context)

    return


def get_grammar_tip(sub_types: list, hint_type: str):
    """Get grammar tip from external text file depending
    on sub types of sentence. Used in Sentence Correction task.

    Args:
    sentence_sub_types -- sub types as list
    hint_type -- "hint" or "grammar_rule" - specifying the output type for the user
    """

    category = sub_types[0]

    # with open('sentence_correction_tips_formating.json') as json_file:
    #     grammar_rules = json.load(json_file)

    path_to_json = "data/adaptivity/sentence_correction_tips_formating.json"
    json_file = open(path_to_json)
    grammar_rules_dict = json.load(json_file)

    print("Category", category, "Value", category.value)
    print("hint type", hint_type)
    print(type(grammar_rules_dict))
    print(list(grammar_rules_dict.keys()))
    print("Number of keys", len(list(grammar_rules_dict.keys())))
    print("category.value Type", type(category.value))
    print("category.value to string", type(str(category.value)))

    return grammar_rules_dict[str(category.value)][hint_type]


def check_selected_user(update):
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    return update.message.from_user.username == sentence_task.get_selected_user()


def _identify_sentence_mistake(update: Update, context: CallbackContext):
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    # Log info about asking for identification
    logger.info('Test information: User asked for error identification')
    # Send message to identify the erroneous word
    # Get words as a list
    sentence_words = sentence_task.get_curr_sentence_words()
    # Send message with keyboard markup that contains the words
    send_message(sentence_task.get_identification_msg(),
                 update, context,
                 reply_markup=create_keyboard_markup(
                     options=sentence_words))
    return state.SEN_CORR_WAIT_FOR_ANSWER_IDENTIFICATION


def evaluate_sentence_mistake_identification(
        update: Update, context: CallbackContext):
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    # First check if message was sent from the selected user
    if not check_selected_user(update):
        # Update adaptive data counter.
        sentence_task.n_messages_non_selected_users += 1
        return state.SEN_CORR_WAIT_FOR_ANSWER_IDENTIFICATION

    # Update adaptive data counter.
    sentence_task.n_messages_selected_user += 1
    # Get the text from the message
    response = update.message.text
    # Check if the response is a word in the sentence and go back to waiting for a response
    if not sentence_task.is_response_in_words(response):
        return state.SEN_CORR_WAIT_FOR_ANSWER_IDENTIFICATION

    # Check against truth
    if sentence_task.check_error_identification(response):
        # Positive feedback
        send_message(
            sentence_task.get_feedback_correct_error_identification(),
            update, context, reply_markup=remove_keyboard_markup)
        # Error correction
        return _correct_sentence_mistake(update, context)

    else:
        # Inform about mistake
        send_message(
            sentence_task.get_feedback_incorrect_error_identification(),
            update, context, reply_markup=remove_keyboard_markup)
        # Update proficiencies and go to next task
        sentence_task.update_proficiencies(correct=False)

        sentence_sub_types = sentence_task.curr_sentence.sub_types

        # Adaptability: display appropriate grammar rule
        send_grammar_feedback(
            update, context, sentence_sub_types, "grammar_rule")

        return _correct_sentence_mistake(update, context)


def _correct_sentence_mistake(update: Update, context: CallbackContext):
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    # Log info about asking for correction
    logger.info('Test information: User asked for sentence correction')
    send_message(sentence_task.get_correction_msg(), update, context)

    return state.SEN_CORR_WAIT_FOR_ANSWER_CORRECTION


def get_message_length(msg):
    return len(msg.split(" "))


def evaluate_sentence_mistake_correction(
        update: Update, context: CallbackContext):

    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))

    # First check if message was sent from the selected user
    if not check_selected_user(update):

        # Update adaptive data counter.
        sentence_task.n_messages_non_selected_users += 1
        return state.SEN_CORR_WAIT_FOR_ANSWER_CORRECTION

    # Update adaptive data counter.
    sentence_task.n_messages_selected_user += 1
    # Get the message
    response = update.message.text

    # Check if message is not longer than one word -> ignore rest
    if not get_message_length(response) == 1:
        return state.SEN_CORR_WAIT_FOR_ANSWER_CORRECTION

    # TODO: Specify when a response from the user is the actual response

    # Check response against truth
    if sentence_task.check_error_correction(response):

        # Increment number of correct responses
        sentence_task.increment_correct_count()

        # Positive feedback
        gif_url = get_gif_link("correct")
        send_animation(gif_url, update, context)
        send_message(
            sentence_task.get_feedback_correct_error_correction(),
            update, context)

        # Update proficiencies
        sentence_task.update_proficiencies(correct=True)
        # Go to next task
        return present_next_task_iteration(update, context)

    else:
        # Inform about mistake
        msg = sentence_task.get_feedback_incorrect()
        if sentence_task.second_chance:
            msg += sentence_task.get_feedback_error_correction()
            sentence_task.second_chance = False
        send_message(msg, update, context)
        # Update proficiencies and go to next task

        sentence_sub_types = sentence_task.curr_sentence.sub_types

        # Give a learning opportunity in case the grammar rule has not been presented yet - present the rule and give one more try
        group_chat_id = get_group_chat_id(update)
        sentence_task = get_sentence_correction_task_of_group(group_chat_id)

        if sentence_sub_types in sentence_task.grammar_rules_used:
            sentence_task.update_proficiencies(correct=False)
            msg = sentence_task.get_feedback_error_correction()
            send_message(msg, update, context, text_markup=True)
            return present_next_task_iteration(update, context)

        else:
            send_grammar_feedback(
                update, context, sentence_sub_types, "grammar_rule")

            msg = sentence_task.get_try_again_msg(
                sentence_task.curr_sentence.get_str())
            msg += "\n" + sentence_task.get_user_selected_msg()
            send_message(msg, update, context, text_markup=True)

            sentence_task.second_chance = True

            return _correct_sentence_mistake(update, context)


def end_task(update: Update, context: CallbackContext, success: bool,
             codeword: str):
    # Log info about proficiency
    logger.info('Test information: End of sentence correction task')
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))

    # Get adaptive data.
    sentence_adaptive_data_entry = sentence_task.get_adaptive_data_entry(
        get_group_chat_id(
            update))
    # Insert db entry.
    insert_sentence_correction_adaptive_data_entry(sentence_adaptive_data_entry)

    sentence_task.log_proficiencies()

    # Send achievement info
    # Inform group
    update.message.reply_text(
        text='Alright, let us check for new achievements ...', quote=False)
    # Get all members of the group
    all_students = sentence_task.all_users
    # Boolean to check if new achievements have been completed (default is False)
    new_achievements_completed = False
    # Check and display achievements for each member
    for student in all_students:
        # Update achievements
        new_achievements = student.update_achievements()
        # Inform about new achievements (TODO: Should be done in private chat maybe -> More difficult to implement)
        if len(new_achievements) > 0:
            # New achievements have been completed
            new_achievements_completed = True
            # Create string with achievement descriptions as new lines
            achievement_text = '\n'.join(map(str, new_achievements))
            # Inform about new achievements
            update.message.reply_text(
                text='Congratulation {}, you earned the following achievements: \n{}'.
                format(
                    student.get_name(),
                    achievement_text),
                quote=False)
    # Send goodbye depending on new achievements being completed
    if new_achievements_completed:
        update.message.reply_text(
            text='Those were all new achievements.', quote=False)
    else:
        update.message.reply_text(
            text='I found no new achievements.', quote=False)

    remove_sentence_correction_task_of_group(get_group_chat_id(update))

    # End the task -> Send dialogue and go to password entering
    return end_task_group(
        update, context, success=success, codeword=codeword,
        state_success=state.SEN_CORR_END_SUCCESS,
        state_fail=state.SEN_CORR_END_FAIL)


def stop_task(update: Update, context: CallbackContext):
    # Log info about proficiency
    logger.info('Test information: End of sentence correction task')
    sentence_task = get_sentence_correction_task_of_group(
        get_group_chat_id(
            update))
    sentence_task.log_proficiencies()

    # Send achievement info
    # Inform group
    update.message.reply_text(
        text='Alright, let us check for new achievements ...', quote=False)
    # Get all members of the group
    all_students = sentence_task.all_users
    # Boolean to check if new achievements have been completed (default is False)
    new_achievements_completed = False
    # Check and display achievements for each member
    for student in all_students:
        # Update achievements
        new_achievements = student.update_achievements()
        # Inform about new achievements (TODO: Should be done in private chat maybe -> More difficult to implement)
        if len(new_achievements) > 0:
            # New achievements have been completed
            new_achievements_completed = True
            # Create string with achievement descriptions as new lines
            achievement_text = '\n'.join(map(str, new_achievements))
            # Inform about new achievements
            update.message.reply_text(
                text='Congratulation {}, you earned the following achievements: \n{}'.
                format(
                    student.get_name(),
                    achievement_text),
                quote=False)
    # Send goodbye depending on new achievements being completed
    if new_achievements_completed:
        update.message.reply_text(
            text="Those were all new achievements.", quote=False)
    else:
        update.message.reply_text(
            text="I found no new achievements.", quote=False)

    remove_sentence_correction_task_of_group(get_group_chat_id(update))

    # Remove the room manager
    remove_room_manager_of_group(get_group_chat_id(update))
    # Send goodbye
    update.message.reply_text(
        text='Goodbye. To start again write /start.', quote=False)

    # Return end state
    return state.SEN_CORR_STOP
