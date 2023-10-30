import os
from unittest import mock

import pytest

from contents.common import DataItem, parse_data


@pytest.mark.parametrize("input_data_items, input_env, expected_dict", [
    ([DataItem('key', 'ENV_VAR', 'str')], {'ENV_VAR': 'value'}, {'key': 'value'}),
    ([DataItem('key', 'ENV_VAR', 'str')], {}, {'key': None}),
    ([DataItem('key', 'ENV_VAR', 'bool')], {'ENV_VAR': 'true'}, {'key': True}),
    ([DataItem('key', 'ENV_VAR', 'bool')], {'ENV_VAR': 'True'}, {'key': True}),
    ([DataItem('key', 'ENV_VAR', 'bool')], {'ENV_VAR': 'False'}, {'key': False}),
    ([DataItem('key', 'ENV_VAR', 'bool')], {'ENV_VAR': 'false'}, {'key': False}),
    ([DataItem('key', 'ENV_VAR', 'shstr')],
     {'ENV_VAR': 'echo "hello world"'}, {'key': ['echo', 'hello world']}),
    ([DataItem('key', 'ENV_VAR', 'shstr')],
     {'ENV_VAR': "echo 'hello world'"}, {'key': ['echo', 'hello world']}),
    ([DataItem('key', 'ENV_VAR', 'shstr')],
     {'ENV_VAR': 'cmd kwarg=val1'}, {'key': ['cmd', 'kwarg=val1']}),
    ([DataItem('key', 'ENV_VAR', 'shstr')],
     {'ENV_VAR': 'cmd kwarg="val2=test"'}, {'key': ['cmd', 'kwarg=val2=test']}),
    ([DataItem('key', 'ENV_VAR', 'shstr')],
     {'ENV_VAR': 'cmd kwarg=\\"val2=test\\"'}, {'key': ['cmd', 'kwarg="val2=test"']}),
    ([DataItem('key', 'ENV_VAR', 'shstr')],
     {'ENV_VAR': "cmd \"kwarg=\\\"{'val2': 'test'}\\\"\""},
     {'key': ['cmd', "kwarg=\"{'val2': 'test'}\""]}),
])
def test_parse_data(input_data_items, input_env, expected_dict):
    with mock.patch.dict(os.environ, input_env):
        actual_dict = parse_data(input_data_items)
        assert actual_dict == expected_dict
