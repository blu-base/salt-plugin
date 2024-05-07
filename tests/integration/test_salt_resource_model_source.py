import logging
import os
import json
from unittest import mock

import pytest

from contents.salt_resource_model_source import main as main_function

log = logging.getLogger(__name__)


def test_targeted_resource_model(rundeck_environment_base, session_minion_id, session_salt_api, capsys):
    assert session_salt_api.is_running()

    env = rundeck_environment_base.copy()

    env.update({
        'RD_CONFIG_TGT': session_minion_id,
    })

    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    out, err = capsys.readouterr()

    assert err == ''

    try:
        out_data = json.loads(out)
        assert isinstance(out_data, dict)
    except json.JSONDecodeError:
        pytest.fail("Failed to parse JSON string")

    # the minion should be part of the returned object
    assert session_minion_id in out_data.keys()
    # the nodename  matches the minionid
    assert out_data.get(session_minion_id, {}).get('nodename') == session_minion_id

    # test shouldn't have run into an error
    assert sys_exit.value.code == 0


def test_glob_targeted_resource_model(rundeck_environment_base, session_minion_id, session_salt_api, capsys):
    assert session_salt_api.is_running()

    env = rundeck_environment_base.copy()

    env.update({
        'RD_CONFIG_TGT': '*',
    })

    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    out, err = capsys.readouterr()
    assert err == ''

    try:
        out_data = json.loads(out)
        assert isinstance(out_data, dict)
    except json.JSONDecodeError:
        pytest.fail("Failed to parse JSON string")

    # the minion should be part of the returned object
    assert session_minion_id in out_data.keys()
    # the nodename  matches the minionid
    assert out_data.get(session_minion_id, {}).get('nodename') == session_minion_id

    # test shouldn't have run into an error
    assert sys_exit.value.code == 0


def test_nonexisting_target_resource_model(rundeck_environment_base, session_salt_api, capsys):
    assert session_salt_api.is_running()

    env = rundeck_environment_base.copy()

    env.update({
        'RD_CONFIG_TGT': 'notaminion',
    })

    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    out, err = capsys.readouterr()
    assert err == ''

    try:
        out_data = json.loads(out)
        assert isinstance(out_data, dict)
    except json.JSONDecodeError:
        pytest.fail("Failed to parse JSON string")

    # the minion should be part of the returned object
    assert 'notaminion' not in out_data.keys()

    # test shouldn't have run into an error
    assert sys_exit.value.code == 0


def test_resource_model_with_tags_and_attributes(rundeck_environment_base, session_minion_id, session_salt_api, capsys):
    assert session_salt_api.is_running()

    env = rundeck_environment_base.copy()

    env.update({
        'RD_CONFIG_TGT': session_minion_id,
        'RD_CONFIG_TAGS': 'os,osrelease',
        'RD_CONFIG_ATTRIBUTES': 'os,osrelease',
    })

    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    out, err = capsys.readouterr()

    assert err == ''

    try:
        out_data = json.loads(out)
        assert isinstance(out_data, dict)
    except json.JSONDecodeError:
        pytest.fail("Failed to parse JSON string")

    # the minion should be part of the returned object
    assert session_minion_id in out_data.keys()
    # the nodename  matches the minionid
    assert out_data.get(session_minion_id, {}).get('nodename') == session_minion_id

    assert len(out_data.get(session_minion_id, {}).get('tags')) == 2
    assert 'os' in out_data.get(session_minion_id, {}).keys()

    # test shouldn't have run into an error
    assert sys_exit.value.code == 0
