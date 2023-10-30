#!/usr/bin/env python -u
import logging
import sys

from pepper import Pepper
from pepper.exceptions import PepperException

from common import DataItem, parse_data, sanitize_dict

log = logging.getLogger(__name__)

# Rundeck environment variables to be parsed
data_items = [
    DataItem('cmd', 'RD_EXEC_COMMAND', 'str'),
    DataItem('node', 'RD_NODE_NAME', 'str'),
    DataItem('runas', 'RD_CONFIG_RUNAS', 'str'),
    DataItem('args', 'RD_CONFIG_CMD_RUN_ARGS', 'shstr'),
    DataItem('url', 'RD_CONFIG_URL', 'str'),
    DataItem('eauth', 'RD_CONFIG_EAUTH', 'str'),
    DataItem('user', 'RD_CONFIG_USER', 'str'),
    DataItem('password', 'RD_CONFIG_PASSWORD', 'str'),
    DataItem('verify_ssl', 'RD_CONFIG_VERIFYSSL', 'bool'),
]


def main():
    # parse environment provided by rundeck
    data = parse_data(data_items)
    log.debug(f"Data: {sanitize_dict(data, ['password'])}")

    # prepare payload contents
    args = [data['cmd']]

    if data['runas'] is not None and data['runas'] != '':
        args.append(f"runas={data['runas']}")

    if data['args'] is not None and data['args'] != '':
        args.extend(data['args'])

    # payload
    low_state = {
        'client': 'local',
        'tgt': data['node'],
        'fun': 'cmd.run',
        'arg': args,
        # full return to get retcode
        'full_return': True,
    }

    # login to api
    client = Pepper(api_url=data['url'], ignore_ssl_errors=not data['verify_ssl'])
    try:
        response = client.login(username=data['user'], password=data['password'], eauth=data['eauth'])
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Logging into API: {response}')

    # sending payload
    try:
        response = client.low(lowstate=low_state)
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Received raw response: {response}')

    # filter response
    minion_response = response.get('return', [{}])[0].get(data['node'])
    data = minion_response.get('ret', 'No response received')
    return_code = minion_response.get('retcode', 1)

    # rundeck reads stdout
    print(data)

    # rundeck reads return code
    sys.exit(return_code)


if __name__ == '__main__':
    main()