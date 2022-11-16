from abc import ABC, abstractmethod


class Task(ABC):

    @abstractmethod
    def get_task_instructions(self):
        pass

    def get_task_variation(self):
        pass
