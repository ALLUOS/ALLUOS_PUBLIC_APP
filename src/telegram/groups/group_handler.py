from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, CreateChannelRequest, EditPhotoRequest
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.types import InputChatUploadedPhoto
import logging
import asyncio

# global variables
group_handler_config = {}
bot_id = ''
logger = logging.getLogger(__name__)


def set_group_handler_config(new_group_handler_config: dict, new_bot_id: str):
    """
    Sets the group handler configuration to use.

    Args:
        new_group_handler_config (dict): A dictionary holding the necessary information for the group handler.
    """
    global group_handler_config
    for key, item in new_group_handler_config.items():
        group_handler_config[key] = item
    global bot_id 
    bot_id = new_bot_id
    logger.debug('New group handler config: ')
    logger.debug(group_handler_config)
    logger.debug(bot_id)


def get_telegram_client():
    """
    Returns the telegram client.
    """
    loop = None
    try:
        loop = asyncio.get_event_loop()
    except:
        # the event loop for this thread was not created yet
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return TelegramClient(group_handler_config['phone_number'] , group_handler_config['telegram_api_id'], group_handler_config['telegram_api_hash'], loop=loop)


def create_telegram_group(group_name: str, group_description: str):
    """
    Creates a telegram group.

    Args:
        group_name (str): The group name.
        group_description (str): The desription of the group.

    Returns:
        The new created group channel.
    """
    group = None
    with get_telegram_client() as client:
        result = client(CreateChannelRequest(title=group_name, about=group_description, megagroup=True))
        group = result.chats[0]
    return group


def add_user_to_channel(channel_id: str, telegram_username: str):
    """
    Adds the given user to the channel.

    Args:
        channel_id (str): The identifier of the channel.
        telegram_username (str): The username of the telegram user to be added.
    """
    logger.info('Add user ({}) to channel ({}).'.format(telegram_username, channel_id))
    with get_telegram_client() as client:
        client(InviteToChannelRequest(channel_id, [telegram_username]))


def add_bot_to_channel(channel_id):
    """
    Adds the bot that is specified in the config-file to the channel.
    """
    logger.info('Add bot ({}) to channel ({}).'.format(bot_id, channel_id))
    add_user_to_channel(channel_id, bot_id)


def get_chat_invite_link(channel):
    """
    Retrives the invitiation link with which a user can join the channel.
    """
    link = ''
    logger.info('Request chat invitation link')
    with get_telegram_client() as client:
        result = client(ExportChatInviteRequest(channel))
        link = result.link
    return link

def set_group_logo(channel_id):
    """
    Upload the group image to the given telethon channel object
    """
    # Get the filepath from config
    global group_handler_config
    filepath = group_handler_config['path_to_group_image']
    try:
        with get_telegram_client() as client:
            channel_entity = client.get_entity(channel_id)
            upload_file_result = client.upload_file(file=filepath)
            input_chat_uploaded_photo = InputChatUploadedPhoto(upload_file_result)
            client(EditPhotoRequest(channel = channel_entity, photo = input_chat_uploaded_photo))
    except Exception as e:
        logger.error(e)
