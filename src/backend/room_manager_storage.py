from .room_manager import RoomManager


singeltons = {}


def get_room_manager_of_group(group_chat_id: str) -> RoomManager:
    """
    Returns the room manager of the group.

    Args:
        group_chat_id (str): The id of the group chat from telegram.

    Returns:
        The RoomManager instance that is used by the group.
    """
    group_singelton = singeltons.get(group_chat_id)
    if not group_singelton:
        group_singelton = RoomManager(group_chat_id)
        singeltons[group_chat_id] = group_singelton
    return group_singelton


def remove_room_manager_of_group(group_chat_id: str):
    """
    Removes the room manager of the group from the list of singeltons.

    Args:
        group_chat_id (str): The id of the group chat from telegram.
    """
    singeltons.pop(group_chat_id, None)
