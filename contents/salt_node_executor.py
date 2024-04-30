#!/usr/bin/env python -u
import logging
import sys

from pepper import Pepper
from pepper.exceptions import PepperException

from common import DataItem, parse_data, sanitize_dict

log = logging.getLogger(__name__)


def main():
    """
    Main function to execute remote commands via Salt-API

    This function retrieves necessary data from environment variables provided by Rundeck.
    """
    # parse environment provided by rundeck
    data_items = [
        DataItem('cmd', 'RD_EXEC_COMMAND', 'str'),
        DataItem('host', 'RD_NODE_HOSTNAME', 'str'),
        DataItem('runas', 'RD_CONFIG_RUNAS', 'str'),
        DataItem('args', 'RD_CONFIG_CMD_RUN_ARGS', 'shstr'),
        DataItem('node-args', 'RD_NODE_SALT_CMD_RUN_ARGS', 'shstr'),
        DataItem('url', 'RD_CONFIG_URL', 'str'),
        DataItem('eauth', 'RD_CONFIG_EAUTH', 'str'),
        DataItem('user', 'RD_CONFIG_USER', 'str'),
        DataItem('password', 'RD_CONFIG_PASSWORD', 'str'),
        DataItem('verify_ssl', 'RD_CONFIG_VERIFYSSL', 'bool'),
        DataItem('log-level', 'RD_JOB_LOGLEVEL', 'str'),
    ]

    data = parse_data(data_items)
    log.debug(f"Data: {sanitize_dict(data, ['password'])}")

    # use rundeck's log level if defined
    if data['log-level'] == 'DEBUG':
        log_level = 'DEBUG'
    else:
        log_level = 'ERROR'
    log.setLevel(logging.getLevelName(log_level))

    # Sanity checks for required input
    for key in ['cmd', 'host', 'url', 'eauth', 'user', 'password']:
        if not data[key]:
            msg = f'No {key} specified. Command not send.'
            log.error(msg)
            sys.exit(1)

    # prepare payload contents
    args = [data['cmd']]

    if data['runas'] is not None and data['runas'] != '':
        args.append(f"runas={data['runas']}")

    if data['args'] is not None and data['args'] != '':
        args.extend(data['args'])

    if data['node-args'] is not None and data['node-args'] != '':
        args.extend(data['node-args'])

    # payload
    low_state = {
        'client': 'local',
        'tgt': data['host'],
        'fun': 'cmd.run',
        'arg': args,
        'full_return': True,  # full return to get retcode
    }

    # login to the API
    client = Pepper(api_url=data['url'], ignore_ssl_errors=not data['verify_ssl'])
    try:
        response = client.login(username=data['user'], password=data['password'], eauth=data['eauth'])
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Logging into API: {response}')

    # send payload
    try:
        response = client.low(lowstate=[low_state])
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Received raw response: {response}')

    # filter response
    minion_response = response.get('return', [{}])[0].get(data['host'], {})
    data = minion_response.get('ret', 'No response received')
    return_code = minion_response.get('retcode', 1)

    # print response to stdout for Rundeck to pickup
    print(data)

    # rundeck reads return code
    sys.exit(return_code)


if __name__ == '__main__':
    main()
