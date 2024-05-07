import pytest

from contents.salt_resource_model_source import string_to_unique_set, prepare_grains, process_tags, process_attributes


@pytest.mark.parametrize(('input_str', 'expected_set'), [
    # Test cases for string_to_unique_set function
    ('', set()),                           # Empty string returns an empty set
    ('abc', set(['abc'])),                 # Single string element returns set with that string
    ('a,b,c', set(['a', 'b', 'c'])),       # Comma-separated string returns set of individual elements
    ('a,,c', set(['a', 'c'])),             # return set without empty elements
    ([], set()),                           # Empty list returns an empty set
    (None, set()),                         # None returns an empty set
    ])
def test_string_to_unique_set(input_str, expected_set):
    assert string_to_unique_set(input_str) == expected_set


@pytest.mark.parametrize(('input_data', 'expected_set'), [
    # Test cases for prepare_grains function

    # Empty input returns set of defaults
    ({}, set(['id', 'cpuarch', 'os', 'os_family', 'osrelease', 'hostname'])),

    # Empty tags and attributes return set of defaults
    ({'tags': '', 'attributes': ''}, set(['id', 'cpuarch', 'os', 'os_family', 'osrelease', 'hostname'])),

    # Tags and attributes with duplicate values return set with default keys and that value
    ({'tags': 'abc', 'attributes': 'abc'}, set(['id', 'cpuarch', 'os', 'os_family', 'osrelease', 'hostname', 'abc'])),

    # Tags and attributes with multiple values return set with default keys and those values
    ({'tags': 'abc', 'attributes': 'a,b'}, set(['id', 'cpuarch', 'os', 'os_family', 'osrelease', 'hostname', 'abc', 'a', 'b'])),
])
def test_prepare_grains(input_data, expected_set):
    assert prepare_grains(input_data) == expected_set


@pytest.mark.parametrize(('needed_tags', 'input_data', 'expected_list'), [
    # Test cases for process_tags function

    (set(), {}, set()),  # Empty needed_tags and empty input_data return an empty set
    (set(), {'a': 'b'}, set()),  # Empty needed_tags and non-empty input_data return an empty set

    # tag with matching key in input_data returns set with the corresponding value
    (set(['plainkey']), {'plainkey': 'a', 'otherkey': 'val'}, set(['a'])),

    # integer tag with matching key in input_data returns set with the corresponding value
    (set(['plainkey']), {'plainkey': 1}, set(['1'])),

    # Single needed tag with list value in input_data returns set with all elements of the list
    (set(['keyoflist']), {'keyoflist': ['a', 'b']}, set(['a', 'b'])),

    # Single needed tag with non-list, non-string value in input_data returns an empty set
    (set(['ignorenested']), {'ignorenested': {'key': 'value'}}, set()),

    # tag not present in input_data returns an empty set
    (set(['missinggrain']), {'othergrain': 'value'}, set()),

    # Nested tag with single string value in input_data returns set with that value
    (set(['nested.plainkey']), {'nested.plainkey': 'a'}, set(['a'])),

    # Nested tag with list value in input_data returns set with all elements of the list
    (set(['nested.keyoflist']), {'nested.keyoflist': ['a', 'b']}, set(['a', 'b'])),

    # Nested tag with non-list, non-string value in input_data returns an empty set
    (set(['nested.ignorenested']), {'nested.ignorenested': {'key': 'value'}}, set()),

    # Duplicate values in single value and list element
    (set(['tag1', 'tag2']), {'tag1': 'val1', 'tag2': ['val1', 'val2']}, set(['val1', 'val2'])),
])
def test_process_tags(input_data, needed_tags, expected_list):
    assert process_tags(input_data, needed_tags) == expected_list


@pytest.mark.parametrize(('needed_attributes', 'input_data', 'reserved_keys', 'expected_list'), [
    # Test cases for process_attributes function

    # Empty Attributes and input_data
    (set(), {}, set(), {}),

    # Empty needed_attributes and non-empty input_data
    (set(), {'unused_key': 'val'}, set(), {}),

    # Attribute present in input_data
    (set(['plainkey']), {'plainkey': 'val', 'otherkey': 'val2'}, set(), {'plainkey': 'val'}),

    # Single attribute with integer value present in input_data
    (set(['plainkey']), {'plainkey': 1, }, set(), {'plainkey': '1'}),

    # Attribute with reserved key present in input_data
    (set(['reservedkey']), {'reservedkey': 'val'}, set(['reservedkey']), {'salt-reservedkey': 'val'}),

    # Attribute not present in input_data
    (set(['missingkey']), {}, set(), {'missingkey': ''}),

    # No values for attribute with list value present in input_data
    (set(['listkey']), {'listkey': ['val1', 'val2']}, set(), {'listkey': ''}),

    # No values for attribute with dict value present in input_data
    (set(['nestedkey']), {'nestedkey': {'key': 'val'}}, set(), {'nestedkey': ''}),
])
def test_process_attributes(input_data, needed_attributes, reserved_keys, expected_list):
    assert process_attributes(input_data, needed_attributes, reserved_keys) == expected_list

