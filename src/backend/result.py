class BackendResult():
    """
    This class can be used to pass results from the backend to the frontend.
    """

    def __init__(self, successful: bool, message: str = ''):
        self.successful = successful
        self.message = message

    
    def is_successful(self) -> bool:
        return self.successful

    
    def get_message(self) -> str:
        return self.message