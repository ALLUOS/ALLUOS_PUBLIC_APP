from email import message
from turtle import up
from telegram import (Update, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (CallbackContext)
import logging
import random
import re
import Levenshtein as lev
from nltk.tokenize import word_tokenize

from ..room_handler import end_task_group, get_room_manager_of_group, remove_room_manager_of_group
from .. import state
from ....backend.tasks.vocabulary_description_storage import get_vocab_description_task_of_group, remove_vocab_description_task_of_group
from ...util import get_group_chat_id, send_message, create_keyboard_markup, send_animation, get_gif_link
from ....backend.db.task import insert_vocabulary_guessing_adaptive_data_entry
from src.misc.debug_mode import is_debug_mode_active


logger = logging.getLogger(__name__)
# TODO: Add logging information

# Set the button for retrial using a new word
NEW_WORD_REPLY_MARKUP = "Give me a new word"
remove_keyboard_markup = ReplyKeyboardRemove()


def task_selection(update: Update, context: CallbackContext):
    """
    Evaluates task selection messages
    """
    if is_debug_mode_active:
        print("task selection()")
    # Get room manager
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))

    # Get selected user who has to chose the task
    selected_usr = group_room_manager.get_selected_user()
    # Check if the message is from the selected user
    print("The selected User is:", selected_usr)
    print("The User who answered was:", update.message.from_user.username)
    if update.message.from_user.username == selected_usr:
        print("You selected the Vocab Desc-Task")
        # Set task in room manager
        group_room_manager.next_task("vocabulary guessing")
        return show_vocab_task_description(update, context)
    else:
        # Wait for message from the correct user -> go back to task selection
        return state.VOCAB_DESC_SEL_WRONG_USER


def show_vocab_task_description(update: Update, context: CallbackContext):
    group_chat_id = get_group_chat_id(update)
    vocab_task = get_vocab_description_task_of_group(group_chat_id)
    send_message(vocab_task.get_task_instructions(),
                 update, context, text_markup=True)

    # send a "lets talk: GIF"
    gif_url = get_gif_link("think")
    send_animation(gif_url, update, context)

    return present_first_task_iteration(update, context)


def send_time_info(context: CallbackContext):
    # get the context of the job that is the update of the calling function
    job = context.job
    update = job.context
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    context.bot.send_message(update.message.chat_id,
                             text=vocab_task.get_time_info())


def timelimit_reached(context: CallbackContext):
    # Send message about reaching the timelimit
    job = context.job
    update = job.context
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    user = vocab_task.get_selected_user()
    context.bot.send_message(
        update.message.chat_id, text=vocab_task.get_time_limit_info().format(
            user))
    # TODO this has to end the current task iteration somehow?


def remove_running_jobs(context: CallbackContext):
    for job in context.job_queue.jobs():
        job.schedule_removal()


def send_new_word(update: Update, context: CallbackContext):

    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    vocab_task.select_word()
    selected_word = vocab_task.get_word().get_word()
    vocab_task.guesses_counter = 0
    vocab_task.letters_to_show_set = set()

    if is_debug_mode_active():
        print("Word to guess:", selected_word)

    # The user gets the reply_keyboard
    send_message(
        vocab_task.get_word_msg(),
        update, context,
        reply_markup=create_keyboard_markup(
            [selected_word, NEW_WORD_REPLY_MARKUP]))

    """    #TODO since the word is sometimes shown for other users (mostly on mac): delete it for them. Did not work. Removes the ReplyKeyboard for everyone.
    all_users = [user.get_telegram_id() for user in vocab_task.get_all_users()]
    print(all_users)
    print(vocab_task.get_selected_user())
    all_users.remove(vocab_task.get_selected_user())
    other_users = all_users
    print(other_users)
    usernames = ""
    for id in other_users:
        usernames += "@"+id+" "
    send_message(
        usernames+"! It's time to guess!",
        update, context,
        reply_markup=ReplyKeyboardRemove())"""

    # stop all current countdowns
    remove_running_jobs(context)
    vocab_task.reset_timelimits()

    # Add jobs to queue to send an alarm about time left
    for reminder_time in vocab_task.get_time_reminders():
        context.job_queue.run_once(
            send_time_info, when=reminder_time, context=update)

    # Add job that terminates the iteration if timelimit has been reached
    context.job_queue.run_once(
        timelimit_reached, when=vocab_task.get_timelimit(), context=update)
    return state.VOCAB_DESC_WAIT_FOR_GUESS


def present_first_task_iteration(update: Update, context: CallbackContext):
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    # Initialize iteration
    vocab_task.next_group_iteration()
    # Send info about first iteration
    send_message(vocab_task.get_first_iteration_info_msg(), update, context)
    # Randomly select a user
    vocab_task.select_next_user()
    # Send new word and wait for guesses
    return send_new_word(update, context)


def present_next_task_iteration(update: Update, context: CallbackContext):
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    # Remove all existing jobs (to avoid duplicate time reminders)
    remove_running_jobs(context)

    # Checkpoint timers simulating the next group iteration method.
    vocab_task.checkpoint_adaptive_data_variables()
    # Get adaptive data.
    vocab_adaptive_data_entry = vocab_task.get_adaptive_data_entry(
        get_group_chat_id(update),
        skipped=False
    )
    # Insert adaptive data.
    insert_vocabulary_guessing_adaptive_data_entry(vocab_adaptive_data_entry)

    # Check if group iteration is finished
    if vocab_task.is_group_iteration_finished():
        # Check if all responses were correct:
        if vocab_task.is_correct_group_iteration():
            # Combine positive feedback and code + Recap of current codeword
            send_message(vocab_task.get_correct_group_iter_feedback(
            ) + "\n" + vocab_task.get_codeword_recap(), update, context)
            # Increment counter
            vocab_task.increment_correct_group_iteration()

        else:
            # Feedback
            send_message(
                vocab_task.get_incorrect_group_iter_feedback(), update, context)
            # Increment counter for incorrect iterations
            vocab_task.increment_incorrect_group_iteration()

        # Reset everything in the iteration over the group
        vocab_task.next_group_iteration()

    # Check if task is finished
    if vocab_task.is_finished():
        # get the global room manager for tracking repeatability
        group_room_manager = get_room_manager_of_group(
            get_group_chat_id(update))
        # increment repetitions counter of this task type
        group_room_manager.increment_task_rep_count("vocabulary guessing")
        # check if task can be repeated in case it was not solved yet, i.e. check if the task repetition counter is less than 2
        if not vocab_task.is_success():
            if group_room_manager._reps_counter["vocabulary guessing"] < 2:
                # add task back to list of available tasks
                group_room_manager.repeat_current_task("vocabulary guessing")
        # End the task and go back to room manager
        return end_task(
            update, context, success=vocab_task.is_success(),
            codeword=vocab_task.get_codeword())
    # Send info about next iteration
    send_message(vocab_task.get_next_iteration_info_msg(), update, context)
    # Randomly select a user
    vocab_task.select_next_user()
    # Send new word and wait for guesses
    return send_new_word(update, context)


def check_selected_user(update):
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    return update.message.from_user.username == vocab_task.get_selected_user()


def get_message_length(msg):
    return len(msg.split(" "))


def check_for_word(update: Update):
    """
    function that checks if the word or its alternatives are in the last send message.
    """
    msg = update.message.text.lower()
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    solution = vocab_task.get_word().get_word().lower()

    # was it the original word?
    contains = re.search(r"^"+solution+r"[!?.]*$", msg)

    # was it one of the alternative words?
    for alternativ in vocab_task.get_word().get_alternatives():
        if not(contains):
            contains = re.search(r"^"+alternativ+r"$", msg)
    return contains


def check_for_forbidden_word(update: Update):
    """
    function that checks if the word or its alternatives are in the last send message.
    """
    msg = update.message.text.lower()
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    solution = vocab_task.get_word().get_word().lower()

    # was it the original word?
    contains = solution in msg

    # was it one of the alternative words?
    for alternativ in vocab_task.get_word().get_alternatives():
        if not(contains):
            contains = alternativ in msg
    return contains


def check_if_close(update: Update):
    """check if the word is close, according to levenshtein"""
    msg = update.message.text.lower()
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    solution = vocab_task.get_word().get_word().lower()

    # is it close to solution?
    close = lev.distance(solution, msg)

    # was it close to one of the alternative words?
    for alternativ in vocab_task.get_word().get_alternatives():
        if not(close):
            close = lev.distance(solution, msg)
    return close < 2


def check_for_guess(update: Update, context: CallbackContext):
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    # Checks if the given update corresponds to a guess and then evaluates it
    # 1. Check if the response is from the selected user
    if check_selected_user(update):
        # Increment adaptive data counter.
        vocab_task.n_messages_selected_user += 1
        # Message is from selected user -> its a description, not a potential guess (or it could be asking for a new word)

        # Check if message contains the "forbidden" word
        # Todo Maybe adjust the result if the user is just close, instead of being really close
        if check_for_forbidden_word(update) or check_if_close(update):
            # Check if timelimit was exceeded
            if vocab_task.check_time_limit():
                # Incorrect because player made an accident
                # Tell the user, that they should not use the word
                send_message(vocab_task.get_word_warning(), update,
                             context, reply_markup=remove_keyboard_markup)
                # In this case, do not update the group proficiency

                # User is send a new word
                return send_new_word(update, context)

            else:
                # Update proficiencies and go to next iteration
                vocab_task.update_proficiencies(correct=False)
                return present_next_task_iteration(update, context)
        elif NEW_WORD_REPLY_MARKUP.lower() == update.message.text.lower():
            # Checkpoint timers simulating the next group iteration method.
            vocab_task.checkpoint_adaptive_data_variables()
            # Get adaptive data.
            vocab_adaptive_data_entry = vocab_task.get_adaptive_data_entry(
                get_group_chat_id(update),
                skipped=True
            )
            # Insert adaptive data.
            insert_vocabulary_guessing_adaptive_data_entry(
                vocab_adaptive_data_entry)
            # Reset adaptive data variables.
            vocab_task.reset_adaptive_data_variables()
            # Remove timers
            remove_running_jobs(context)
            # Send new word
            return send_new_word(update, context)

        else:
            # Store description text.
            vocab_task.description_texts.append(update.message.text.lower())
            # Valid description, go back to waiting for guesses
            return state.VOCAB_DESC_WAIT_FOR_GUESS

    else:
        # Increment adaptive data counter.
        vocab_task.n_messages_non_selected_users += 1

        # Message is from another user -> potential guess

        # Check if response contains the current word
        if check_for_word(update):

            # Correct guess
            # Check if timelimit has not been reached
            if vocab_task.check_time_limit():

                # Send information about correct response
                send_message(
                    vocab_task.get_feedback_correct_guess(),
                    update, context, reply_markup=remove_keyboard_markup,
                    quote=True, delay=False)

                # Increment counter of correct answers
                vocab_task.increment_correct_count()
                # Update proficiencies and go to next iteration
                vocab_task.update_proficiencies(correct=True)
                # Go to next iteration
                return present_next_task_iteration(update, context)

        elif check_if_close(update):
            send_message(
                "The word '" + update.message.text.lower() +
                "' is written similar to the correct answer! Check your spelling!",
                update, context, speaker="elias")
            # Invalid guess -> Wait for next guess
            return state.VOCAB_DESC_WAIT_FOR_GUESS

        else:
            # Invalid guess -> increase the counter (only if it is a single word)
            last_msg = update.message.text
            if len(last_msg.split()) == 1:
                vocab_task.guesses_counter += 1

            print(vocab_task.guesses_counter)
            send_hints(update, context)

            return state.VOCAB_DESC_WAIT_FOR_GUESS


def send_hints(update: Update, context: CallbackContext):
    """
    Returns a different type of hint depending on the number of mistakes
    the group has made:
      After 3 mistakes: the group gets the name of the word's category
      After 5 mistakes: the groups gets the length of the word
      After 9 mistakes: the group gets the word displayed like a hangman game with one letter revealed
    """

    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    selected_word = vocab_task.get_word().get_word()

    if vocab_task.guesses_counter == 3:

        # give a hint with category
        category_names = {
            21: "Free Time",
            22: "Culture & Arts",
            23: "Education & Society",
            24: "Nature & Society",
            25: "Food",
            26: "Body & Soul",
            27: "Household & Buildings"}

        topic_category = vocab_task.get_curr_proficiency_sub_types()[0].value
        send_message(random.choice(vocab_task.get_word_category_hint()).format(
            category_names[topic_category]), update, context, speaker="elias")

        return state.VOCAB_DESC_WAIT_FOR_GUESS

    elif vocab_task.guesses_counter == 5:
        # give a hint with the word length
        word_length = len(selected_word)
        send_message(random.choice(vocab_task.get_word_length_hint()).format(
            word_length), update, context, speaker="elias")

        return state.VOCAB_DESC_WAIT_FOR_GUESS

    elif vocab_task.guesses_counter >= 9 and (vocab_task.guesses_counter < 9+(len(selected_word)/2)):
        # give a random letter, hangman style

        letter_to_show = random.choice(list(selected_word))
        vocab_task.letters_to_show_set.add(letter_to_show)

        hangman_hint = ""

        for letter in selected_word:

            if letter not in vocab_task.letters_to_show_set:
                hangman_hint += "_ "
            else:
                hangman_hint += letter + " "

        send_message(random.choice(vocab_task.get_hangman_hint()).format(
            hangman_hint), update, context, speaker="elias")


def stop_task(update: Update, context: CallbackContext):
    """
    Stops a task prematurely via the given command
    """
    # Log info about proficiency
    logger.info('Test information: End of vocab guessing task')
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))
    vocab_task.log_proficiencies()
    # Remove existing jobs if there are any
    remove_running_jobs(context)
    # Send achievement info
    # Inform group
    update.message.reply_text(
        text='Alright, let us check for new achievements ...', quote=False)
    # Get all members of the group
    all_students = vocab_task.all_users
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
                text="Congratulation {}, you earned the following achievements: \n{}".
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
    remove_vocab_description_task_of_group(get_group_chat_id(update))

    # Remove the room manager
    remove_room_manager_of_group(get_group_chat_id(update))
    # Send goodbye
    update.message.reply_text(
        text='Goodbye. To start again write /start.', quote=False)

    # Return end state
    return state.VOCAB_DESC_STOP


def end_task(update: Update, context: CallbackContext, success: bool,
             codeword: str):
    # Log info about proficiency
    logger.info('Test information: End of vocab guessing task')
    vocab_task = get_vocab_description_task_of_group(get_group_chat_id(update))

    # Checkpoint timers simulating the next group iteration method.
    vocab_task.checkpoint_adaptive_data_variables()
    # Get adaptive data.
    vocab_adaptive_data_entry = vocab_task.get_adaptive_data_entry(
        get_group_chat_id(update),
        skipped=False
    )

    vocab_task.log_proficiencies()
    # Remove existing jobs if there are any
    remove_running_jobs(context)
    # Send achievement info
    # Inform group
    update.message.reply_text(
        text='Alright, let us check for new achievements ...', quote=False)
    # Get all members of the group
    all_students = vocab_task.all_users
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
                text="Congratulation {}, you earned the following achievements: \n{}".
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
    remove_vocab_description_task_of_group(get_group_chat_id(update))

    # End the task -> Send dialogue and go to password entering
    return end_task_group(
        update, context, success=success, codeword=codeword,
        state_success=state.VOCAB_DESC_END_SUCCESS,
        state_fail=state.VOCAB_DESC_END_FAIL)
