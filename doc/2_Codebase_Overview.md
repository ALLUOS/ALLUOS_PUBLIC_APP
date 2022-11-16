[< Previous step](1_Introduction.md) | [Home](../README.md) | [Next step >](3_Usage.md)

---

# Codebase Overview

## Explanation:
- ``abc/``: represents a (sub)directory
- ``abc.xy``: represents a file 



## Codebase:
- ``data/`` : Folder for data required in the app, such as audio intros, proficiency infos and the task data itself
- ``doc/`` : Folder for the documentation files
- ``logs/``: Will be created after the first start of the app.  
Contains the log files of the bot and testing information:
   - ``ALL_bot.log``
   - ``test_info.log``
- ``src/``: Source folder of the application
  - ``backend/``: All backend related files
    - ``adaptability/``: Contains the files related to the adaptability of the application
    - ``db/``: Contains all the database files (setup, connection, task data etc.)
    - ``entities/``: Contains the classes for the entities used in the app.
      - ``group.py``: Represents a group entity from the database.
      - ``sentence.py``: Represents a sentence entity from the database for the sentence correction task
      - ``student.py``: Represents a student/user of the app.  
      Contains all user related information such as ID, name and proficiency level
      - ``task.py``: Represents a task entity from the database
      - ``word.py``: Represents a word entity from the database for the vocabulary description task
    - ``tasks/``: Folder contains the main task handling files for the respective tasks
      - ``base_task.py``: Abstract base class for any task
      - ``sequential_task.py``: Abstract parent class of any sequential task (like sentence correction and 
      vocab guessing)
      - ``sentence_correction.py``File that handles the backend of the sentence correction task
      - ``vocabulary_description.py`` File that handles the backend of the vocabulary description task
    - ``result.py``: File used for transporting results from backend to frontend
    - ``room_manager.py``: Manages the transition and instantiation of the different tasks for a single group.
    - ``tools.py``: Some general helper functions for the backend
  - ``bot/``:
    - ``filters/``: Contains telegram message filters to classify input
    - ``handler/``: Contains the basic conversation handlers and the conversation states
      - ``private_base.py``: Base conversation handler for private interaction
      - ``room_handler.py``: Conversation handler for task organisation in the group
      - ``states.py``: Instantiation of conversational states
      - ``task/``: Contains the task specific conversation handlers used during a task
        - ``sen_corr_handler.py``
        - ``vocab_desc_handler.py``
    - `bot.py`: File for creating and starting the bot
    - `util.py`: Utility functions for group chats
  - ``misc/``: Miscellaneous files 
  - ``telegram/``: Contains a `demo_script.py` and a `group_handler.py` file used for group-database communication
- ``.gitignore``: Standard gitignore file 
- ``bot.config``: Main configuration file for the bot which has to be passed when starting the application
- ``environment.yml``: YML-File for creating a working environment with all the necessary packages
- ``main.py``: The main file of the application from which the application is started
- ``README.md``: Main ReadMe file
- ``test_bot.config``: Bot configuration file for test purposes
