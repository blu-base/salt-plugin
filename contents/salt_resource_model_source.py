#!/usr/bin/env python -u
import logging
import sys
import json

from pepper import Pepper
from pepper.exceptions import PepperException

from common import DataItem, parse_data, sanitize_dict

log = logging.getLogger(__name__)


def configure_logging(log_level):
    """
    Configure logging based on the provided log level.
    """
    log_level = 'ERROR' if log_level != 'DEBUG' else 'DEBUG'
    log.setLevel(logging.getLevelName(log_level))


def validate_required_inputs(data):
    """
    Validate required data items provided by Rundeck
    """
    # Sanity checks for required input
    for key in ['url', 'eauth', 'user', 'password']:
        if not data[key]:
            msg = f'No {key} specified. Command not send.'
            log.error(msg)
            sys.exit(1)

    # Ensure defaults if parameter not set
    if data['tgt'] is None:
        data['tgt'] = '*'


def tag_grains(data):
    grains = set()
    if data.get('tags') is not None:
        grains = set(data['tags'].split(','))

    return grains


def attributes_grains(data):
    grains = set()
    if data.get('attributes') is not None:
        grains = set(data.get('attributes', '').split(','))
    return grains


def prepare_grains(data):
    """
    Prepare grains for tags and attributes.
    """
    needed_grains = set(['id', 'cpuarch', 'os', 'os_family', 'osrelease'])

    needed_tags  = tag_grains(data)
    needed_attributes = attributes_grains(data)

    log.debug(f'Tag grains: {needed_tags}')
    log.debug(f'Attribute grains: {needed_attributes}')

    return needed_grains | needed_tags | needed_attributes


def collect_minions_grains(data, all_needed_grains):
    """
    Execute low state API call and return minions response.
    """
    # Prepare payload
    low_state = {
        'client': 'local',
        'tgt': data['tgt'],
        'fun': 'grains.item',
        'arg': list(all_needed_grains),
        'kwarg': {},
        'full_return': True,
    }

    if data['timeout'] is not None:
        low_state['kwarg']['timeout'] = data['timeout']
    if data['gather-timeout'] is not None:
        low_state['kwarg']['gather_job_timeout'] = data['gather-timeout']

    log.debug(f'Compiled low_state: {low_state}')

    # Login to the API
    client = Pepper(api_url=data['url'], ignore_ssl_errors=not data['verify_ssl'])
    try:
        response = client.login(username=data['user'], password=data['password'], eauth=data['eauth'])
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Logging into API: {response}')

    # Send payload
    try:
        response = client.low(lowstate=[low_state])
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Received raw response: {response}')

    minions = response.get('return', [{}])[0]
    return minions


def get_os_family(os_family):
    """
    Map OS family to a standardized format.
    """
    os_family_map = {
        'Linux': 'unix',
        'AIX': 'unix',
        'MacOS': 'unix',
        'VMware': 'unix',
        'Windows': 'windows'
    }
    return os_family_map.get(os_family, os_family)


def process_tags(grains, needed_tags):
    """
    Extract tags from grains.
    """
    tags = []
    for tag in needed_tags:
        tag_value = grains.get(tag, None)
        if isinstance(tag_value, list):
            tags.extend(tag_value)
        elif tag_value:
            tags.append(tag_value)
    return tags


def process_attributes(grains, needed_attributes, reserved_keys):
    """
    Process attributes from grains.
    """
    processed_attributes = {}
    for attribute in needed_attributes:
        attribute_name = f'salt-{attribute}' if attribute in reserved_keys else attribute
        attribute_value = grains.get(attribute)
        if attribute_value:
            if isinstance(attribute_value, (str, int)):
                processed_attributes[attribute_name] = attribute_value
            else:
                log.warning(f'The grain {attribute} is not a string. Nested values are not supported attribute values.')
    return processed_attributes


def generate_resource_model(minions, data):
    """
    Generate resource model from minions and grains data.
    """
    reserved_keys = {'nodename', 'hostname', 'username', 'description', 'tags', 'osFamily', 'osArch', 'osName',
                     'osVersion', 'editUrl', 'remoteUrl'}

    resource_model = {}
    for minion, ret in minions.items():
        nodename = minion if not data['prefix'] else f"{data['prefix']}{minion}"

        grains = ret['ret']
        model = {
            'nodename': nodename,
            'osArch': 'x86_64' if grains['cpuarch'] in ['x86_64', 'AMD64'] else grains['cpuarch'],
            'osName': grains['os'],
            'osVersion': grains['osrelease'],
            'osFamily': get_os_family(grains['os_family']),
            'tags': process_tags(grains, tag_grains(data))
        }

        processed_attributes = process_attributes(grains, attributes_grains(data), reserved_keys)
        model.update(processed_attributes)

        resource_model[nodename] = model

    return resource_model


def main():
    """
    Main function to generate ressource model

    This function retrieves necessary data from environment variables provided by Rundeck.
    """
    # parse environment provided by rundeck
    data_items = [
        DataItem('tgt', 'RD_CONFIG_TGT', 'str'),
        DataItem('tags', 'RD_CONFIG_TAGS', 'str'),
        DataItem('attributes', 'RD_CONFIG_ATTRIBUTES', 'str'),
        DataItem('prefix', 'RD_CONFIG_REFIX', 'str'),
        DataItem('timeout', 'RD_CONFIG_TIMEOUT', 'int'),
        DataItem('gather-timeout', 'RD_CONFIG_GATHER_TIMEOUT', 'int'),
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
    configure_logging(data['log-level'])

    # sanity checks
    validate_required_inputs(data)

    # queue the Salt-API
    all_needed_grains = prepare_grains(data)
    minions = collect_minions_grains(data, all_needed_grains)

    # compile the Rundeck Resource Model
    resource_model = generate_resource_model(minions, data)

    # print response to stdout for Rundeck to pickup
    print(json.dumps(resource_model))

    sys.exit(0)


if __name__ == '__main__':
    main()

