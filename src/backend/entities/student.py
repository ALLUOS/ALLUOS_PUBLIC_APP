import logging

from ..adaptability.proficiency import Proficiency
from..achievements.all_achievements import create_all_achievements
from collections import defaultdict

logger = logging.getLogger(__name__)

class Student():

    def __init__(self, id, telegram_id, name, proficiency = None, data = None, paths = None):
        # TODO: Define students attributes
        self.id = id
        self.telegram_id = telegram_id
        self.name = name
        self.path_selected = False
        if paths is None:
            self.paths = []
        else:
            self.paths = paths
        # Initialize proficiency
        if proficiency is not None:
            self.proficiency = proficiency
        else:
            self.proficiency = Proficiency()
        # Initialize user data
        if data:
            self.data = data
        else:
            self.data = {}
        # Initialize achievements
        self.completed_achievements = []
        self.open_achievements = []
        self.initialize_achievements()


    def __str__(self):
        return "Student(ID: {}, Telegram-ID: {}, Name: {})".format(self.id, self.telegram_id, self.name)

    def __repr__(self):
        return str(self)

    def get_telegram_id(self):
        """
        Returns the telegram username that doubles as an ID
        """
        return self.telegram_id


    def get_id(self):
        """
        Returns the (internal) user-ID
        """
        return self.id


    def get_name(self):
        """
        Returns the name of the user
        """
        return self.name

    def get_proficiency(self):
        """
        Returns the proficiency class of this user
        """
        return self.proficiency

    def save_path(self, path):
        """
        Saves a path to the student and show he did choose this turn by turning path_selected to True
        """
        self.paths.append(path)
        self.path_selected = True
        logger.debug("Saved path user {}".format(self.get_name()))
        # TODO: Save to database.

    def get_paths(self):
        """
        Returns the path selected by the user
        """
        return self.paths

    def get_proficiency_as_list(self):
        """
        Returns the proficiency as a list that includes the user ID
        """
        return self.proficiency.get_as_list(self.id)

    def get_grammar_proficiency(self):
        """
        Returns the grammar proficiency dictionary of this user
        """
        return self.proficiency.get_grammar_proficiency()

    def get_vocab_proficiency(self):
        """
        Returns the vocab proficiency dictionary of this user
        """
        return self.proficiency.get_vocab_proficiency()

    def get_avg_grammar_proficiency(self):
        """
        Returns the average grammar proficiency value of this user
        """
        return self.proficiency.get_grammar_avg()

    def get_avg_vocab_proficiency(self):
        """
        Returns the average vocab proficiency value of this user
        """
        return self.proficiency.get_vocab_avg()

    def get_discussion_proficiency(self):
        """
        Returns the discussion proficiency value of this user
        """
        return self.proficiency.get_discussion_proficiency()

    def update_proficiency(self, proficiency_sub_types, correct, group_update = False):
        """
        Updates all proficiencies provided in the list proficiency_sub_types
        """
        self.proficiency.update_proficiencies(proficiency_sub_types, correct, group_update = group_update)

    def increment_data(self, field, increment = 1):
        """
        Add the given increment to the user data field
        """
        # Check if field exists, else create it with the increment 
        if field in self.data.keys():
            self.data[field] = self.data[field] + increment
        else:
            self.data[field] = increment

    def update_data(self, field, value):
        """
        Updates the user data field with the given value
        """
        self.data[field] = value

    def get_data_value(self, field):
        """
        Return the value for a given data field. If the field does not exists yet, return 0
        """
        # Check if field exists, else create it with the increment 
        if field in self.data.keys():
            return self.data[field]
        else:
            return 0

    def get_data(self):
        """
        Returns the full dictionary of user data
        """
        return self.data

    def get_data_as_list(self):
        """
        Returns the user data as a list for database input
        """
        # Create list for data   
        data = []
        for field, value in self.data.items():
            data.append((self.id, field, value))        
        return data

    def update_achievements(self):
        """ Check open achievements for completion and add to list of completed achievements, also return list of newly completed achievements """
        # List for newly completed achievements
        new_achievements = []        
        # Go through all open achievments
        for achievement in self.open_achievements:
            # Add achievement to list of newly completed if condition is met and remove it from open achievements
            if achievement.is_completed():
                new_achievements.append(achievement)
        # Remove from open achievements
        for achievement in new_achievements:
            self.open_achievements.remove(achievement)                
        # Add all new achievement to list of completed for user
        self.completed_achievements.extend(new_achievements)
        # Return list of new achievements
        return new_achievements

    def initialize_achievements(self):
        """
        Initializes all achievements based on current user data
        """
        # Add all existing achievements to list of open achievements 
        self.open_achievements = create_all_achievements(self)        
        # Update achievements based on user data
        _ = self.update_achievements()

    def get_open_achievements(self):
        """ Returns all non-completed achievements as a list """
        return self.open_achievements

    def get_next_open_achievements(self):
        """ Returns only the next levels of each achievement type as a list """
        # Sort open achievements into different lists based on type
        achievements_dict = defaultdict(list)
        for achievement in self.open_achievements:
            achievements_dict[type(achievement)].append(achievement)
        # Create empty list of next achievements
        next_achievements = []
        # Add first element (sorted on threshold) for each achievement type to list
        for (_, achievements) in achievements_dict.items():
            # Sort achievements
            achievements.sort()
            # Append first element 
            next_achievements.append(achievements[0])
        # Return the results
        return next_achievements

    def get_completed_achievements(self):
        """ Returns all completed achievements as a list """
        return self.completed_achievements

    