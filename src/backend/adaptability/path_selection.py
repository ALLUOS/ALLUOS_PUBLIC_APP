import json
import logging
import datetime
from ..entities.paths import PathCollection, Path
from ..db.student import get_n_recent_adaptive_data_entries


logger = logging.getLogger(__name__)
with open("./data/proficiency/path_info.json", "r") as f:
    path_info = json.load(f)

def select_paths_based_on_user(user_id:str, task_name:str) -> list:
    """
    Return a list of path options
    based on the student's previous
    performance.

    Parameters
    ---------
        user : str
            Telegram handle for relevant user.
        task_name : str
            Name of task for which we wish to
            propose adaptivity options.

    Returns
        paths : list
            Enum object cast to list,
            summarizing suggested paths.
    """
    paths = list(PathCollection)
    records = get_n_recent_adaptive_data_entries(user_id, task_name)
    longest_duration_sub_type = identify_longest_duration_sub_type(records)
    mask = [98, 99, longest_duration_sub_type, 0]
    # apply basic mask to preserve enumerables
    paths = [e for e in paths if e.value in mask]

    return paths

def identify_longest_duration_sub_type(records:list) -> int:
    """
    Identifies the sub-type which took
    the longest over the input records,
    returning the relevant sub-type ID.

    Parameters
    ---------
        records : list[tuple]
            List of records as
            duration, subtype tuples.

    Returns
    ---------
        sub_type : int
            Sub-type ID.
    """
    try:
        merge_dict = {s: [] for s in list(zip(*records))[1]}
        for duration, sub_type in records:
            # convert duration to seconds
            seconds = duration.total_seconds()
            merge_dict[sub_type].append(seconds)

        # As each sub-type key has a list of durations as value, we average
        # these durations to a single value
        res = [(s, sum(durs) / len(durs)) for s, durs in merge_dict.items()]
        res_sorted = sorted(res, key=lambda x: x[1], reverse=True)

        return res_sorted[0][0]
    except IndexError:
        #if records were empty we get an index error above
        #0 is None in the PathCollection enum
        return 0

def path_messages(path_list):
    """
    path_list: A list of Path enums

    Returns a list with all the messages associated with the paths in path list
    # TODO Should be looked up in the data base instead of creating this dictionary each time.
    """
    path_messages = []
    message_dict = create_path_msg_dict()
    for path in path_list:
        path_messages.append(message_dict[path.name])

    return path_messages

def create_path_msg_dict():
    """
    Returns a dictionary of messages to all available paths
    """
    messages = {k:v['message'] for k,v in path_info.items()}

    return messages

def get_all_paths():
    return list(PathCollection)
