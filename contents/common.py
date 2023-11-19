import logging
import os

from shlex import split as shlex_split
from typing import List, NamedTuple, Optional, Any, Sequence


log = logging.getLogger(__name__)


def str_to_bool(string: str) -> Optional[bool]:
    """
    Convert a string to a boolean value.

    :param string: The input string to convert to a boolean.

    :returns: The boolean value parsed from the input string, input string is
              None or empty, or could not be converted.
    """
    if string is None:
        return None

    string = string.strip().lower()

    if string in ('true', '1', 'yes', 'on'):
        return True

    if string in ('false', '0', 'no', 'off'):
        return False

    return None


class DataItem(NamedTuple):
    """
    Represents a variable provided by Rundeck. To be used as interface to
    parsed by parse_data

    :param key: A shorthand for the Rundeck environment variable
    :type key: str
    :param env_var: The name of the environment variable provided by Rundeck
    :type env_var: str
    :param data_type: The data type of the configuration value (e.g., 'str',
                      'bool', 'shstr').
    :type data_type: str

    """
    key: str
    env_var: str
    data_type: str


def parse_data(data_items: List[DataItem]) -> dict:
    """
    Parse data items and retrieve values from environment variables provided by Rundeck.

    :param data_items: A list of DataItem objects representing configuration items.
    :type data_items: List[DataItem]

    :returns: A dictionary with data keys and their corresponding values.
    :rtype: dict
    """
    log.debug(f'Parsing data_items: {data_items}')
    data = {}
    for item in data_items:
        env_value: Any = os.getenv(item.env_var, None)
        if env_value is not None:
            if item.data_type == "bool":
                env_value = str_to_bool(env_value)
            elif item.data_type == "shstr":
                env_value = shstr(env_value)
            elif item.data_type == "int":
                env_value = int(env_value)
            data[item.key] = env_value
        else:
            log.debug(f'data_item {item.key} is empty')
            data[item.key] = None
    return data


def shstr(command: str) -> List[str]:
    """
    Parse a command provided as string by Rundeck into a list of individual
    arguments as required by the Salt-API.

    :param command: String provided by Rundeck
    : return: List of command elements
    """

    try:
        args = shlex_split(command)
    except ValueError as exception:
        log.error(str(exception))
        return []
    except SyntaxError as exception:
        log.error(str(exception))
        return []

    return args


def sanitize_dict(input_dict: dict, sensitive_keys: Sequence[str]) -> dict:
    """
    Replaces sensitive keys within a dictionary with a placeholder. e.g. used for debug output.
    """
    sanitized_dict = input_dict.copy()
    for key in sensitive_keys:
        if key in sanitized_dict:
            sanitized_dict[key] = "********"

    return sanitized_dict
