class TestInformationFilter():
    """
    A filter that checks whether the log record begins with "Test information:"
    """

    def __init__(self):
        self.log_begin = 'Test information:'


    def filter(self, record):
        """
        Checks whether the log record begins with "Test information:".

        Args:
            record (LogRecord): The log record to filter.

        Returns:
            A boolean indicating whether the record should be logged or not.
        """
        return record.getMessage().startswith(self.log_begin)