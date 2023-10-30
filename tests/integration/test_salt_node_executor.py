import logging
import os
from unittest import mock

import pytest

from contents.salt_node_executor import main as main_function

log = logging.getLogger(__name__)


def test_trivial_command(rundeck_environment_base, session_minion_id, session_salt_api, capsys):
    assert session_salt_api.is_running()

    env = rundeck_environment_base.copy()

    env.update({
        'RD_EXEC_COMMAND': 'echo hello world',
        'RD_NODE_NAME': session_minion_id,
    })

    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    out, err = capsys.readouterr()

    assert out == 'hello world\n'
    assert err == ''

    # test shouldn't have run into an error
    assert sys_exit.value.code == 0


def test_jinja_command(rundeck_environment_base, session_minion_id, session_salt_api, capsys):
    assert session_salt_api.is_running()

    env = rundeck_environment_base.copy()

    env.update({
        'RD_EXEC_COMMAND': "echo {{ grains['id'] }}",
        'RD_NODE_NAME': session_minion_id,
        'RD_CONFIG_CMD_RUN_ARGS': 'template=jinja timeout=10'
    })

    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    out, err = capsys.readouterr()

    assert out == f'{session_minion_id}\n'
    assert err == ''

    # test shouldn't have run into an error
    assert sys_exit.value.code == 0
