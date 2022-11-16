import emoji
from abc import ABCMeta, abstractmethod

class Achievement:
    __metaclass__ = ABCMeta
    
    def __init__(self, name, completion_text, progress_text, achievement_emoji, threshold, student, completed = False):
        """
        Initializes the achievement with all relevant information
        """
        self.name = name # The name of the achievement 
        self.completion_text = completion_text # Text displayed upon completion of the achievement
        self.progress_text = progress_text # Text displayed for achievement in progress
        self.emoji = achievement_emoji # Emoji for visualization of the achievement
        self.threshold = threshold # Numeric threshold for completion of achievement
        self.student = student # The student object this achievement belongs to (as a pointer)
        self.completed = completed # If the achievement has already been completed, this would be True
        

    def is_completed(self):
        """
        Checks if the achievement has been fulfilled previously or the condition has now been met
        """
        if not self.completed:
            if self.get_progress() >= self.threshold:
                self.completed = True            
        return self.completed

    def get_description(self):
        """ Returns a string with the completion text if completed or progress text if not completed """
        if self.completed:
            return self.get_completed_description()
        else:
            return self.get_progress_description()

    def get_threshold(self):
        return self.threshold

    def get_completed_description(self):
        """ Returns the description for a completed achievement """
        return self.completion_text

    def get_progress_description(self):
        """ Returns the current progress for an uncompleted achievement """
        return self.progress_text.format(self.get_progress())

    # Abstract function to be implemented by the individual achievement subclasses
    @abstractmethod   
    def get_progress(self):
        """ Return value of desired student data e.g. number of consecutive days of app usage """
        pass

    # Functions to display achievements in an easy pythonic way
    def __str__(self):
        return emoji.emojize(self.emoji + " " + self.name + ": " + self.get_description(), use_aliases = True)

    def __repr__(self):
        return str(self)

    # Function for sorting achievements easily
    def __lt__(self, other):
        return self.get_threshold() < other.get_threshold()