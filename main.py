from src.bot.util import send_message


import sys
import json
import logging
import psycopg2
import psycopg2.extras
from pathlib import Path

from src.misc.log_filter import TestInformationFilter
from src.backend.db.connection import set_db_config
from src.telegram.groups.group_handler import set_group_handler_config, get_telegram_client

# ensure that the logging directory exists
Path('./logs').mkdir(parents=True, exist_ok=True)
# setup the logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create console handler that a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
# create a file handler that logs even debug messages
fh = logging.FileHandler('logs/ALL_bot.log', 'w', 'utf-8')
fh.setLevel(logging.DEBUG)
# create a file handler that logs just the test information
testInfoHandler = logging.FileHandler('logs/test_info.log', 'w', 'utf-8')
testInfoHandler.setLevel(logging.DEBUG)
testInfoHandler.addFilter(TestInformationFilter())
# create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
testInfoHandler.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)
logger.addHandler(testInfoHandler)

if __name__ == '__main__':
    print("Starting the bot.")
    # check arguments
    if len(
            sys.argv) == 2 and (
            sys.argv[1] == '-h' or sys.argv[1] == '--help'):
        print('Usage example: python3 main.py bot.config.json')
        sys.exit(0)
    if len(sys.argv) != 2:
        print('Wrong arguments. Please provide a configuration file')
        sys.exit(1)

    # load configuration
    with open(sys.argv[1]) as config_file:
        config = json.load(config_file)

    # set the database configuration
    logger.info('Set the database configuration')
    # pass the schema to the database config
    config['db_connection']['options'] = config['db_connection'][
        'options'].format(config['database_schema'])
    set_db_config(config['db_connection'])
    logger.info('Finished database configuration')
    # we need to register the usage of uuids
    psycopg2.extras.register_uuid()

    # Recreate or update to the new database schema
    from src.backend.db.setup import create_or_update_tables, delete_schema, create_schema_and_tables, insert_base_data
    if config['delete_data_and_recreate_database_schema']:
        logger.info('Delete the data and recrete the database schema')
        delete_schema(config['database_schema'])
        create_schema_and_tables(config['database_schema'])
        insert_base_data(config['data_files'])
    elif config['update_database_schema']:
        logger.info('Update database to new database schema')
        create_or_update_tables()

    # load the configuration of the group handler
    set_group_handler_config(config['telegram_api'], config['bot']['id'])
    logger.info('Start the group handler for the first time.')
    with get_telegram_client() as client:
        pass
        # nothing to do here, just make sure that the telegram client is ready

    # Initialize the task phrases
    from src.backend.tasks.sentence_correction import set_sentence_correction_task_phrases
    from src.backend.tasks.vocabulary_description import set_vocab_guessing_task_phrases
    from src.backend.tasks.discussion import set_discussion_task_phrases
    from src.backend.tasks.listening import set_listening_task_phrases

    set_sentence_correction_task_phrases(config['phrase_files'])
    set_vocab_guessing_task_phrases(config['phrase_files'])
    set_discussion_task_phrases(config['phrase_files'])
    set_listening_task_phrases(config['phrase_files'])

    # Initialize story scenario
    from src.bot.handler.room_handler import set_sentence_correction_task_phrases
    set_sentence_correction_task_phrases(config['phrase_files'])

    # Initialize achievement lists
    from src.backend.achievements.all_achievements import set_achievement_list
    set_achievement_list(config['achievement_file'])

    # Intialize the private chat handler
    from src.bot.handler.private_base import set_phone_number
    set_phone_number(config['telegram_api']['phone_number'])

    # start the bot
    from src.bot.bot import start_bot

    while True:
        try:
            start_bot(
                token=config['bot']['token'],
                bot_data_filename=config['bot']['data_file'])
        except:
            continue
