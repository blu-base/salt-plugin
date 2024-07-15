#!/usr/bin/env python -u
import logging
import sys
import json

from pepper import Pepper
from pepper.exceptions import PepperException

from common import DataItem, parse_data, sanitize_dict

log = logging.getLogger(__name__)


def configure_logging(log_level: str):
    """
    Configure logging based on the provided log level.
    """
    log_level = 'ERROR' if log_level != 'DEBUG' else 'DEBUG'
    log.setLevel(logging.getLevelName(log_level))


def validate_required_inputs(data: dict):
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


def string_to_unique_set(src: str) -> set:
    """
    Return set with unique values from input string.
    """
    if isinstance(src, str):
        ret = set(src.split(','))
        ret.discard('')

        return ret

    return set()


def prepare_grains(data: dict) -> set:
    """
    Prepare grains for tags and attributes.
    """
    needed_grains = set(['id', 'cpuarch', 'os', 'os_family', 'osrelease', 'hostname'])

    needed_tags  = string_to_unique_set(data.get('tags', None))
    needed_attributes = string_to_unique_set(data.get('attributes', None))

    log.debug(f'Tag grains: {needed_tags}')
    log.debug(f'Attribute grains: {needed_attributes}')

    return needed_grains | needed_tags | needed_attributes


def prepare_pillar(data: dict) -> set:
    """
    Prepare pillar for tags and attributes.
    """
    needed_tags = string_to_unique_set(data.get('pillar-tags', None))
    needed_attributes = string_to_unique_set(data.get('pillar-attributes', None))

    log.debug(f'Tag pillar: {needed_tags}')
    log.debug(f'Attribute pillar: {needed_attributes}')

    return needed_tags | needed_attributes

def login(data):
    # Login to the API
    client = Pepper(api_url=data['url'], ignore_ssl_errors=not data['verify_ssl'])
    try:
        response = client.login(username=data['user'], password=data['password'], eauth=data['eauth'])
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Logging into API: {response}')

    return client


def collect_minions_grains(client, data, all_needed_grains):
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
        low_state['timeout'] = data['timeout']
    if data['gather-timeout'] is not None:
        low_state['gather_job_timeout'] = data['gather-timeout']

    log.debug(f'Compiled low_state: {low_state}')

    # Send payload
    try:
        response = client.low(lowstate=[low_state])
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Received raw response: {response}')

    minions = response.get('return', [{}])[0]
    return minions


def collect_minions_pillar(client, data, all_needed_pillar):
    """
    Execute low state API call and return minions response.
    """
    # Prepare payload
    low_state = {
        'client': 'local',
        'tgt': data['tgt'],
        'fun': 'pillar.item',
        'arg': list(all_needed_pillar),
        'kwarg': {},
        'full_return': True,
    }

    if data['timeout'] is not None:
        low_state['timeout'] = data['timeout']
    if data['gather-timeout'] is not None:
        low_state['gather_job_timeout'] = data['gather-timeout']

    log.debug(f'Compiled low_state: {low_state}')

    # Send payload
    try:
        response = client.low(lowstate=[low_state])
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Received raw response: {response}')

    minions = response.get('return', [{}])[0]
    return minions


def get_os_family(os_family: str) -> str:
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


def process_tags(metadata: dict, needed_tags: set) -> set:
    """
    Extract tags from grains or pillar.
    """
    tags = set()
    for tag in needed_tags:
        tag_value = metadata.get(tag)
        if tag_value is None:
            continue
        if isinstance(tag_value, (str, int, float)):
            tags.add(str(tag_value))
        elif isinstance(tag_value, list):
            tags.update(str(elem) for elem in tag_value if isinstance(elem, (str, int, float)))
        else:
            log.warning(f'The tag {tag} is not a supported type (str, int, float, or a list of these types)')
    return tags


def process_attributes(metadata, needed_attributes, reserved_keys):
    """
    Process attributes from grains or pillar.
    """
    processed_attributes = {}
    for attribute in needed_attributes:
        attribute_name = f'salt-{attribute}' if attribute in reserved_keys else attribute
        attribute_value = metadata.get(attribute, '')
        if isinstance(attribute_value, (str, int, float)):
            processed_attributes[attribute_name] = str(attribute_value)
        else:
            log.warning(f'The attribute {attribute} is not a string. Nested values are not supported attribute values.')
            processed_attributes[attribute_name] = ''

    return processed_attributes


def generate_resource_model(minions_grains, minions_pillar, data):
    """
    Generate resource model from minions and grains data.
    """
    reserved_keys = {'nodename', 'hostname', 'username', 'description', 'tags', 'osFamily', 'osArch', 'osName',
                     'osVersion', 'editUrl', 'remoteUrl'}

    resource_model = {}
    for minion, ret in minions_grains.items():
        nodename = minion if data['prefix'] is None else f"{data['prefix']}{minion}"

        if not isinstance(ret, dict) or ret.get('ret') is None:
            log.warning(f'Minion {minion} does not have parsable return')
            continue

        grains = ret['ret']

        model = {
            'nodename': nodename,
            'hostname': minion,
            'osArch': 'x86_64' if grains['cpuarch'] in ['x86_64', 'AMD64'] else grains['cpuarch'],
            'osName': grains['os'],
            'osVersion': grains['osrelease'],
            'osFamily': get_os_family(grains['os_family']),
            'tags': list(process_tags(grains, string_to_unique_set(data['tags'])))
        }

        processed_attributes = process_attributes(grains, string_to_unique_set(data['attributes']), reserved_keys)
        model.update(processed_attributes)

        resource_model[nodename] = model

    # process pillar for valid nodes
    for nodename, value in resource_model.items():
        minion = value['hostname']
        pillar = minions_pillar.get(minion, {}).get('ret', {})

        # extend existing tags
        pillar_tags = process_tags(pillar, string_to_unique_set(data['pillar-tags']))
        resource_model[nodename]['tags'] += pillar_tags

        # append attributes
        processed_attributes = process_attributes(pillar, string_to_unique_set(data['pillar-attributes']), reserved_keys)
        resource_model[nodename].update(processed_attributes)

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
        DataItem('pillar-tags', 'RD_CONFIG_PILLAR_TAGS', 'str'),
        DataItem('pillar-attributes', 'RD_CONFIG_PILLAR_ATTRIBUTES', 'str'),
        DataItem('prefix', 'RD_CONFIG_PREFIX', 'str'),
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
    all_needed_pillar = prepare_pillar(data)

    # open session with Salt-API
    client = login(data)

    # collect metadata
    grains = collect_minions_grains(client, data, all_needed_grains)
    pillar = {}
    if len(all_needed_pillar) > 0:
        pillar = collect_minions_pillar(client, data, all_needed_pillar)

    # compile the Rundeck Resource Model
    resource_model = generate_resource_model(grains, pillar, data)

    # print response to stdout for Rundeck to pickup
    print(json.dumps(resource_model))

    sys.exit(0)


if __name__ == '__main__':
    main()

