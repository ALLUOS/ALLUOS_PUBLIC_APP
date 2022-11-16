from os import path
from src.backend.tools import load_phrases
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
import logging

from ..room_handler import get_room_manager_of_group, end_task_group, prompt_task_selection, remove_room_manager_of_group
from .. import state
from ....backend.tasks.discussion import Discussion
from ...util import get_gif_link, get_group_chat_id, send_animation, send_message, create_keyboard_markup, send_image
from ....backend.db.task import insert_discussion_adaptive_data_entry

from ....backend.db.student_data import update_student_data
from ....backend.db.student_proficiency import update_student_proficiency
from ....backend.db.task import create_discussion_task
from ....backend.room_manager_storage import get_room_manager_of_group

logger = logging.getLogger(__name__)


def show_discussion_task_description(update: Update, context: CallbackContext):
    # first, start the task
    group_chat_id = get_group_chat_id(update)
    discussion_task = get_discussion_task_of_group(group_chat_id)

    # set random discussion text
    discussion_task.set_random_discussion_text()

    # then, show the description to the user
    send_message(discussion_task.get_task_instructions(),
                 update, context, text_markup=True)

    return present_text(update, context)


def present_text(update: Update, context: CallbackContext):
    discussion_task = get_discussion_task_of_group(get_group_chat_id(update))

    # send text to group
    send_message(discussion_task.get_text(), update, context)
    remove_running_jobs(context)
    discussion_task.reset_times()
    # set a timer until you send the question to let the users read the text
    context.job_queue.run_once(present_q1, when=30, context=update)

    return state.DISCUSS_Q1


def present_q1(context: CallbackContext):

    update = context.job.context
    discussion_task = get_discussion_task_of_group(get_group_chat_id(update))
    # send gif
    gif_url = get_gif_link('lets_talk')
    send_animation(gif_url, update, context)
    # send question 1 to the users
    send_message("<b>"+discussion_task.get_question()+"</b>",
                 update, context, text_markup=True)
    # Reset time and add new timelimit job
    discussion_task.reset_times()

    # Add 6 reminder-Messages, spread by 30 seconds
    for i in range(1, 7):
        context.job_queue.run_once(
            send_reminder, when=30 * i - 30, context=update)

    # Add a "You reached your Timelimit"-Message
    context.job_queue.run_once(
        timelimit_reached, when=30 + discussion_task.get_timelimit(),
        context=update)

    # Set state
    return state.DISCUSS_Q1


def present_q2(update: Update, context: CallbackContext):
    discussion_task = get_discussion_task_of_group(get_group_chat_id(update))
    discussion_task.increment_iteration()
    # Print question 2 for the users
    send_message("<b>"+discussion_task.get_question()+"</b>",
                 update, context, delay=True)
    # Reset job queue and add new timelimit job
    remove_running_jobs(context)
    discussion_task.reset_times()
    # Add 6 reminder-Messages, spread by 30 seconds
    for i in range(1, 7):
        context.job_queue.run_once(
            send_reminder, when=30*i-30, context=update)

    # Add a "You reached your Timelimit"-Message
    context.job_queue.run_once(
        timelimit_reached, when=discussion_task.get_timelimit(), context=update)
    # Set state
    return state.DISCUSS_Q2


def present_q3(update: Update, context: CallbackContext):
    discussion_task = get_discussion_task_of_group(get_group_chat_id(update))
    discussion_task.increment_iteration()
    # Print question 3 for the users
    send_message("<b>"+discussion_task.get_question()+"</b>",
                 update, context, delay=True)
    # Reset job queue and add new timelimit job
    remove_running_jobs(context)
    discussion_task.reset_times()
    # Add 6 reminder-Messages, spread by 30 seconds
    for i in range(1, 7):
        context.job_queue.run_once(
            send_reminder, when=30*i-30, context=update)

    # Add a "You reached your Timelimit"-Message
    context.job_queue.run_once(
        timelimit_reached, when=discussion_task.get_timelimit(),
        context=update)
    # Set state
    return state.DISCUSS_Q3


def handle_q1(update: Update, context: CallbackContext):
    discussion_task = get_discussion_task_of_group(get_group_chat_id(update))
    discussion_task.evaluate_user_input(
        update.message.from_user.username, update.message.text, task_no=1)
    # if time limit is exceeded or word amount reached go to next question
    if discussion_task.check_time_limit():
        discussion_task.send_intermediate_feedback(update, context, task_no=1)
        remove_running_jobs(context)
        return present_q2(update, context)
    return state.DISCUSS_Q1


def handle_q2(update: Update, context: CallbackContext):
    discussion_task = get_discussion_task_of_group(get_group_chat_id(update))
    discussion_task.evaluate_user_input(
        update.message.from_user.username, update.message.text, task_no=2)
    # if time limit is exceeded or word amount reached go to next question
    if discussion_task.check_time_limit():
        discussion_task.send_intermediate_feedback(update, context, task_no=2)
        remove_running_jobs(context)
        return present_q3(update, context)
    return state.DISCUSS_Q2


def handle_q3(update: Update, context: CallbackContext):
    discussion_task = get_discussion_task_of_group(get_group_chat_id(update))
    discussion_task.evaluate_user_input(
        update.message.from_user.username, update.message.text, task_no=3)
    # if time limit is exceeded or word amount reached go to next question
    if discussion_task.check_time_limit():
        discussion_task.send_final_feedback(update, context)
        remove_running_jobs(context)
        group_room_manager = get_room_manager_of_group(
            get_group_chat_id(update))
        # increment repetitions counter
        group_room_manager.increment_task_rep_count("discussion")
        # check if task can be repeated, i.e. check if repetition counter is less than 2
        if discussion_task.is_correct() == 0:
            if group_room_manager._reps_counter["discussion"] < 2:
                # add the discussion task back to the list
                group_room_manager.repeat_current_task("discussion")
        return end_task(
            update, context, success=discussion_task.is_correct(),
            codeword=discussion_task.get_codeword())
    return state.DISCUSS_Q3


def task_selection(update: Update, context: CallbackContext):
    """
    Evaluates task selection messages
    """
    # Get room manager
    group_room_manager = get_room_manager_of_group(get_group_chat_id(update))
    # Get selected user who has to chose the task
    selected_usr = group_room_manager.get_selected_user()  # TODO finish
    # Check if the message is from the selected user
    if update.message.from_user.username == selected_usr:
        # Set task in room manager
        group_room_manager.next_task("discussion")
        return show_discussion_task_description(update, context)
    else:
        # Wait for message from the correct user -> go back to task selection
        return state.DISCUSS_SEL_WRONG_USER


def end_task(update: Update, context: CallbackContext, success: bool,
             codeword: str):
    # Log info about proficiency
    logger.info('Test information: End of discussion task')
    discuss_task = get_discussion_task_of_group(get_group_chat_id(update))
    # Remove existing jobs if there are any
    remove_running_jobs(context)
    # Send achievement info
    # Inform group
    update.message.reply_text(
        text='Alright, let us check for new achievements ...', quote=False)
    # Get all members of the group
    all_students = discuss_task.all_users
    # Boolean to check if new achievements have been completed (default is False)
    new_achievements_completed = False
    # Check and display achievements for each member
    for student in all_students:
        # Get the adaptive data entry.
        entry = discuss_task.get_adaptive_data_entry(
            student.get_id(),
            student.get_telegram_id(),
            get_group_chat_id(update))
        insert_discussion_adaptive_data_entry(entry)
        # Update proficiency values based on performance and survey data.
        # discuss_task.update_user_proficiency_based_on_task_performance_and_survey(student) #TODO include later, taken out just for the demo
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
    remove_discussion_task_of_group(get_group_chat_id(update))

    # End the task -> Send dialogue and go to password entering
    return end_task_group(
        update, context, success=success, codeword=codeword,
        state_success=state.DISCUSS_END_SUCCESS,
        state_fail=state.DISCUSS_END_FAIL)


def stop_task(update: Update, context: CallbackContext):
    # Log info about proficiency
    logger.info('Test information: End of discussion task')
    discuss_task = get_discussion_task_of_group(get_group_chat_id(update))
    # discuss_task.log_proficiencies()#TODO implement
    # Remove existing jobs if there are any
    remove_running_jobs(context)
    # Send achievement info
    # Inform group
    update.message.reply_text(
        text='Alright, let us check for new achievements ...', quote=False)
    # Get all members of the group
    all_students = discuss_task.all_users
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
    remove_discussion_task_of_group(get_group_chat_id(update))

    # Remove the room manager
    remove_room_manager_of_group(get_group_chat_id(update))
    # Send goodbye
    update.message.reply_text(
        text='Goodbye. To start again write /start.', quote=False)

    # Return end state
    return state.DISCUSS_STOP


def remove_running_jobs(context: CallbackContext):
    for job in context.job_queue.jobs():
        job.schedule_removal()


def timelimit_reached(context: CallbackContext):
    # Send message about reaching the timelimit
    job = context.job
    update = job.context
    discussion_task = get_discussion_task_of_group(get_group_chat_id(update))
    context.bot.send_message(update.message.chat_id,
                             text=discussion_task.get_time_limit_info())
    # TODO this has to end the current task iteration somehow?


def send_reminder(context: CallbackContext):
    """
    Sends a countdown-image.
    """
    job = context.job
    update = job.context
    discussion_task = get_discussion_task_of_group(get_group_chat_id(update))
    path_to_countdown = discussion_task.create_reminder()
    send_image(update, path_to_countdown)


singeltons = {}


def get_discussion_task_of_group(group_chat_id: str) -> Discussion:
    """
    Returns the DiscussionTask of the group.
    Args:
        group_chat_id (str): The id of the group chat from telegram.
    Returns:
        The DiscussionTask instance that is used by the group.
    """
    group_singelton = singeltons.get(group_chat_id)
    if not group_singelton:

        # get the students that participate in the task
        active_users = get_room_manager_of_group(
            group_chat_id).get_joined_student_list()
        group_singelton = create_discussion_task(active_users)
        singeltons[group_chat_id] = group_singelton
    return group_singelton


def remove_discussion_task_of_group(group_chat_id: str):
    """
    Removes the VocabularyDescription of the group from the list of singeltons.
    Args:
        group_chat_id (str): The id of the group chat from telegram.
    """
    # Save data to the database
    for student in get_room_manager_of_group(group_chat_id).get_joined_student_list():
        update_student_proficiency(student)
        update_student_data(student)
    # Remove singleton
    singeltons.pop(group_chat_id, None)
