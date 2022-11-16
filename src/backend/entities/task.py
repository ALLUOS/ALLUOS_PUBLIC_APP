class Task():
    """
    Represents a task entity from the database.
    """


    def __init__(self, id: int, name: str, min_num_of_players: int, num_of_iterations: int):
        """
        Initializes a new task entity.

        Args:
            id (int): The identifer from the database.
            name (str): The name of the task.
            min_num_of_players (int): The minimun number of players needed for this task.
            num_of_iterations (int): The number of iterations.
        """
        self.id = id
        self.name = name
        self.min_num_of_players = min_num_of_players
        self.num_of_iterations = num_of_iterations


    def get_id(self):
        """
        Returns the id of the task. 
        """
        return self.id

    
    def get_name(self):
        """
        Returns the name of the task.
        """
        return self.name


    def get_min_num_of_players(self):
        """
        Returns the minumum of players needed.
        """
        return self.min_num_of_players


    def get_num_of_iterations(self):
        """
        Returns the number of iterations.
        """
        return self.num_of_iterations