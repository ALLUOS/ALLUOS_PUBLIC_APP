from .achievement import Achievement
import emoji
import datetime

from ..db.student_data import update_student_data
from ...misc.date_tools import date_to_int, int_to_date


class ConsecutiveDaysStreak(Achievement):

    def __init__(self, name, completion_text, progress_text, achievement_emoji, threshold, student, completed = False):
        """
        Initializes the achievement with all relevant information
        """
        self.name = name # The name of the achievement
        self.completion_text = completion_text # Text displayed upon completion of the achievement
        self.progress_text = progress_text # Text displayed for achievement in progress
        self.emoji = emoji.emojize(achievement_emoji) # Emoji for visualization of the achievement
        self.threshold = threshold # Numeric threshold for completion of achievement
        self.student = student # The student object this achievement belongs to (as a pointer)
        self.completed = completed # If the achievement has already been completed, this would be True

    # Implement abstract method for this achievement
    def get_progress(self):
        """ Gets the current number of consecutive days of app usage for a user """

        # Get current date in date format
        today = datetime.date.today()

        # Get different streak information from DB
        last_played = self.student.get_data_value('last_played')
        if not last_played or last_played == 0:
            # Unknown last play date -> Start streak now
            self.student.update_data(field='last_played', value=date_to_int(today))
            self.student.update_data(field='consecutive_days', value=1)
            return 1

        highest_streak = self.student.get_data_value('highest_streak')
        if not highest_streak or highest_streak == 0:
            # if not exists, initiate highest streak with 1
            self.student.update_data(field='highest_streak', value=1)

        current_streak = self.student.get_data_value('consecutive_days')

        # Convert last played to date
        last_played = int_to_date(self.student.get_data_value('last_played'))

        if today == last_played:
            # return self.student.get_data_value('consecutive_days')
            return current_streak

        elif today - last_played == datetime.timedelta(days=1):
            # Update Data
            current_streak += 1
            self.student.increment_data('consecutive_days')
            self.student.update_data(field='last_played', value=date_to_int(today))

            if current_streak > highest_streak:
                self.student.update_data(field='highest_streak', value=current_streak)

            # And Update DB entry
            update_student_data(self.student)

            # return self.student.get_data_value('consecutive_days')
            return current_streak

        elif today - last_played > datetime.timedelta(days=1):
            # Update Data
            current_streak = 1
            self.student.update_data(field='consecutive_days', value=current_streak)
            self.student.update_data(field='last_played', value=date_to_int(today))

            # And Update DB entry
            update_student_data(self.student)

            # return self.student.get_data_value('consecutive_days')
            return current_streak

    def is_completed(self):

        if not self.completed:

            current_streak = self.get_progress()
            highest_streak = self.student.get_data_value('highest_streak')

            if not highest_streak or highest_streak == 0:
                # if not exists, initiate highest streak with 1
                self.student.update_data(field='highest_streak', value=1)
                highest_streak = 1

            if max(highest_streak, current_streak) >= self.threshold:
                self.completed = True

        return self.completed

