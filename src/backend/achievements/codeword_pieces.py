from .achievement import Achievement
import emoji

class CodewordPiecesCollected(Achievement):

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
        return self.student.get_data_value('codeword_pieces_collected')