from telegram.ext import (Updater, PicklePersistence)
from .handler import room_manager_conv_handler, private_base_conv_handler, tutorial_conv_handler, faq_conv_handler


def _create_bot(token: str, bot_data_filename: str) -> Updater:
    """
    Creates a new bot instance from the given token and loads the bot data from the file.

    Args:
        token (str): The bot's token.
        bot_data_filename (str): The name of the pickle-file in which the user and chat data of the bot is stored.

    Returns:
        An updater object.
    """
    # Create the Updater
    updater = Updater(token, use_context=True, request_kwargs={
                      'read_timeout': 15, 'connect_timeout': 20})

    # get the dispatcher to register handlers
    dp = updater.dispatcher
    dp.add_handler(room_manager_conv_handler)
    dp.add_handler(private_base_conv_handler)
    dp.add_handler(tutorial_conv_handler)
    dp.add_handler(faq_conv_handler)

    return updater


def start_bot(token: str, bot_data_filename: str):
    """
    Starts a new bot.
    Args:
        token (str): The bot's token.
        bot_data_filename (str): The name of the pickle-file in which the user data of the bot is stored.
    """
    try:
        updater = _create_bot(token, bot_data_filename)

        # start the Bot
        print("The bot has started")
        updater.start_polling()
        updater.idle()
    finally:
        print("The Bot has been ended, using CTRL+C")
