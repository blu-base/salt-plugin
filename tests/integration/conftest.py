# Import python libraries
import logging
import os.path
import shutil
import tempfile

# Import pytest libraries
import pytest
from pytestskipmarkers.utils import ports
from saltfactories.utils import random_string

# Import Salt Libraries

# Import Pepper libraries

log = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def salt_api_port():
    """
    Returns an unused localhost port for the api port
    """
    return ports.get_unused_localhost_port()


@pytest.fixture
def tokfile():
    tokdir = tempfile.mkdtemp()
    yield os.path.join(tokdir, 'peppertok.json')
    shutil.rmtree(tokdir)


@pytest.fixture
def output_file():
    """
    Returns the path to the salt master configuration file
    """
    out_dir = tempfile.mkdtemp()
    yield os.path.join(out_dir, 'output')
    shutil.rmtree(out_dir)


@pytest.fixture(scope='session')
def session_master_factory(request, salt_factories, session_master_config_overrides):
    return salt_factories.salt_master_daemon(
        random_string("master-"),
        overrides=session_master_config_overrides
    )


@pytest.fixture(scope='session')
def session_master(session_master_factory):
    with session_master_factory.started():
        yield session_master_factory


@pytest.fixture(scope='session')
def session_master_config_overrides(request, salt_api_port, salt_api_backend):
    return {
        salt_api_backend: {
            'port': salt_api_port,
            'disable_ssl': True,
        },
        'external_auth': {
            'sharedsecret': {
                'pepper': [
                    '.*',
                    '@jobs',
                    '@wheel',
                    '@runner',
                ],
            },
        },
        'sharedsecret': 'pepper',
        'token_expire': 94670856,
        'ignore_host_keys': True,
        'ssh_wipe': True,
        'netapi_enable_clients': [
            'local',
            'local_async',
            'local_subset',
            'ssh',
            'runner',
            'runner_async',
            'wheel',
            'wheel_async',
            'run'
        ]
    }


@pytest.helpers.register
def remove_stale_minion_key(master, minion_id):
    key_path = os.path.join(master.config["pki_dir"], "minions", minion_id)
    if os.path.exists(key_path):
        os.unlink(key_path)
    else:
        log.debug("The minion(id=%r) key was not found at %s", minion_id, key_path)


@pytest.fixture(scope='session')
def session_minion_factory(session_master_factory):
    """
    Return a factory for a randomly named minion connected to master.
    """
    minion_factory = session_master_factory.salt_minion_daemon(random_string("minion-"))
    minion_factory.after_terminate(
        pytest.helpers.remove_stale_minion_key, session_master_factory, minion_factory.id
    )
    return minion_factory


@pytest.fixture(scope='session')
def session_minion(session_master, session_minion_factory):  # noqa
    assert session_master.is_running()
    with session_minion_factory.started():
        yield session_minion_factory


@pytest.fixture(scope='session')
def session_minion_id(session_minion):
    return session_minion.id


@pytest.fixture(scope='session')
def salt_api_backend(request):
    """
    Return the salt-api backend (cherrypy or tornado)
    """
    backend = request.config.getoption('--salt-api-backend')
    if backend is not None:
        return backend

    backend = request.config.getini('salt_api_backend')
    if backend is not None:
        return backend

    return 'rest_cherrypy'


@pytest.fixture(scope='session')
def session_salt_api_factory(session_master_factory):
    return session_master_factory.salt_api_daemon()


@pytest.fixture(scope='session')
def session_salt_api(session_master, session_salt_api_factory):
    assert session_master.is_running()
    with session_salt_api_factory.started():
        yield session_salt_api_factory


@pytest.fixture
def rundeck_environment_base(salt_api_port):
    env = {
        'RD_CONFIG_USER': 'pepper',
        'RD_CONFIG_PASSWORD': 'pepper',
        'RD_CONFIG_EAUTH': 'sharedsecret',
        'RD_CONFIG_URL': f'http://localhost:{salt_api_port}',
        'RD_CONFIG_VERIFYSSL': 'False'
    }

    return env
