from .streaks import ConsecutiveDaysStreak
from .codeword_pieces import CodewordPiecesCollected
from ...backend.tools import load_phrases
import json

# Create empty dict to store achievement info in
achievement_json = {}

def set_achievement_list(filepath):
    global achievement_json
    achievement_json = load_phrases(filepath)

def create_all_achievements(student):
    """
    Creates a list of all achievements for the current student
    """
    # Init empty list
    achievements = []    
    
    # Init all achievements with the given data and the student object and add them to the list
    # Streak achievements
    for streak in achievement_json["Streaks"]:
        achievements.append(ConsecutiveDaysStreak(name = streak["name"], completion_text = streak["completion_text"], progress_text = streak["progress_text"], achievement_emoji = streak["achievement_emoji"], threshold = streak["threshold"], student = student, completed = False))
    # Codeword pieces achievements
    for code_word in achievement_json["Codewords"]:
        achievements.append(CodewordPiecesCollected(name = code_word["name"], completion_text = code_word["completion_text"], progress_text = code_word["progress_text"], achievement_emoji = code_word["achievement_emoji"], threshold = code_word["threshold"], student = student, completed = False))
    
    # Return list of achievements
    return achievements