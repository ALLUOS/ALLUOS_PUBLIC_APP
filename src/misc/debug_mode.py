import sys
import json


def is_debug_mode_active():
    debug_options = _get_debug_from_bot_config()
    if debug_options is None:
        return False
    is_debug_active = debug_options['is_active']
    return is_debug_active


def _get_debug_from_bot_config():
    with open(sys.argv[1]) as config_file:
        config = json.load(config_file)
        return config.get('debug', None)


def activate_debug():
    with open(sys.argv[1]) as config_file:
        config = json.load(config_file)
        return config.set('debug', True)
