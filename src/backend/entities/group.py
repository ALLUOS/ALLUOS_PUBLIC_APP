class Group():
    """
    Represents a group entity from the database.
    """

    def __init__(self, id: int, chat_id:str, invitation_url: str, invitation_code: str):
        """
        Initializes a new group entity.

        Args:
            id (int): The identifier of the group from the database.
            chat_id (str): The telegram chat identifier of the group.
            invitation_url (str): The invitation url to the group.
            invitation_code (str): The invitation code with which a user can join the group.
        """
        self.id = id
        self.chat_id = chat_id
        self.invitation_url = invitation_url
        self.invitation_code = invitation_code

    
    def get_id(self):
        """
        Returns the identifier of the group from the database.
        """
        return self.id

    
    def get_chat_id(self):
        """
        Returns the thelegram chat identifier of the group.
        """
        return self.chat_id


    def get_invitation_code(self):
        """
        Returns the invitation code of the group.
        """
        return self.invitation_code


    def get_invitation_url(self):
        """
        Returns the invitation url to this chat.
        """
        return self.invitation_url
    