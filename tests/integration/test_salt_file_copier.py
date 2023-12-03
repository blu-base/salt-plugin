import logging
import os
import secrets

from unittest import mock
import pytest


from contents.salt_file_copier import main as main_function

log = logging.getLogger(__name__)


@pytest.mark.parametrize("hostname", [None, ""])
def test_empty_hostname(rundeck_environment_base, hostname, capsys, mocker):

    env = rundeck_environment_base.copy()

    dest = '/path/to/dest/file.txt'
    src = '/path/to/src/file.txt'

    env.update({
        'RD_FILE_COPY_FILE': src,
        'RD_FILE_COPY_DESTINATION': dest,
    })

    if hostname is not None:
        env.update({
            'RD_NODE_HOSTNAME': hostname
        })

    # ignore logging from function
    mocker.patch("contents.salt_file_copier.log")

    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    out, err = capsys.readouterr()

    assert out == f'{dest}\n'
    assert 'There is no hostname defined for the Node. File not send.' in err
    # test shouldn't have run into an error
    assert sys_exit.value.code == 1


def test_empty_source_file(rundeck_environment_base, session_minion_id, session_salt_api, tmp_path, capsys, mocker):
    assert session_salt_api.is_running()

    env = rundeck_environment_base.copy()

    dest = tmp_path / 'dest_file.txt'

    env.update({
        'RD_NODE_HOSTNAME': session_minion_id,
        'RD_FILE_COPY_FILE': "",
        'RD_FILE_COPY_DESTINATION': str(dest),
    })

    # ignore logging from function
    mocker.patch("contents.salt_file_copier.log")

    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    out, err = capsys.readouterr()

    assert out == f'{str(dest)}\n'
    assert 'No source file specified. No File send.' in err

    # test shouldn't have run into an error
    assert sys_exit.value.code == 1


def test_empty_destination_file(rundeck_environment_base, session_minion_id, session_salt_api, tmp_path, capsys, mocker):
    assert session_salt_api.is_running()

    env = rundeck_environment_base.copy()

    src = tmp_path / 'src_file.txt'

    env.update({
        'RD_NODE_HOSTNAME': session_minion_id,
        'RD_FILE_COPY_FILE': str(src),
        'RD_FILE_COPY_DESTINATION': "",
    })

    # ignore logging from function
    mocker.patch("contents.salt_file_copier.log")

    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    out, err = capsys.readouterr()

    assert out == f'\n'
    assert 'No destination file specified. No File send.' in err

    # test shouldn't have run into an error
    assert sys_exit.value.code == 1


@pytest.mark.parametrize("file_length", [1000, 1024*3072])
def test_file_transfer(rundeck_environment_base, session_minion_id, session_salt_api, file_length, tmp_path, capsys):
    assert session_salt_api.is_running()

    env = rundeck_environment_base.copy()

    dest = tmp_path / 'dest_file.txt'
    src = tmp_path / 'src_file.txt'

    env.update({
        'RD_NODE_HOSTNAME': session_minion_id,
        'RD_FILE_COPY_FILE': str(src),
        'RD_FILE_COPY_DESTINATION': str(dest),
    })

    # create test file
    random_content = secrets.token_bytes(file_length)
    with open(src, 'wb') as f:
        f.write(random_content)

    # transfer file
    with mock.patch.dict(os.environ, env):
        with pytest.raises(SystemExit) as sys_exit:
            main_function()

    # read and compare destination file
    assert dest.is_file()
    with open(dest, 'rb') as f:
        assert f.read() == random_content

    out, err = capsys.readouterr()

    assert out == f'{str(dest)}\n'
    assert err == ''

    # Clean up: Remove both the source and copied files
    src.unlink()
    dest.unlink()

    # test shouldn't have run into an error
    assert sys_exit.value.code == 0
