from enum import Enum
import pandas as pd

from src.misc.constants import (
    SEN_CORR_TASK_NAME, VOC_DESC_TASK_NAME, DISCUSSION_TASK_NAME,
    LISTENING_TASK_NAME)


class Task_cols(Enum):
    ID = 'id'
    NAME = "name"
    MIN_NUM_OF_PLAYERS = "min_num_of_players",
    NUM_OF_ITERATIONS = "num_of_iterations"


def _create_task_definitions():
    column_names = [Task_cols.ID, Task_cols.NAME,
                    Task_cols.MIN_NUM_OF_PLAYERS, Task_cols.NUM_OF_ITERATIONS]

    task_rows = [
        (1, SEN_CORR_TASK_NAME, 1, 4),
        (2, VOC_DESC_TASK_NAME, 2, 4),
        (3, DISCUSSION_TASK_NAME, 2, 1),
        (4, LISTENING_TASK_NAME, 1, 3)]

    # having min num of players as 1 leads to
    # a premature starting of the group journey with select a task
    task_debug_rows = [(1, SEN_CORR_TASK_NAME, 1, 1),  # [(1, SEN_CORR_TASK_NAME, 1, 1),
                       (2, VOC_DESC_TASK_NAME, 2, 1),
                       (3, DISCUSSION_TASK_NAME, 3, 1),
                       (4, LISTENING_TASK_NAME, 1, 1)]  # (4, LISTENING_TASK_NAME, 1, 1)]

    task_df = pd.DataFrame(task_rows, columns=column_names)
    task_debug_df = pd.DataFrame(task_debug_rows, columns=column_names)

    return (task_df, task_debug_df)


TASK_DEF_DF, TASK_DEBUG_DEF_DF = _create_task_definitions()
