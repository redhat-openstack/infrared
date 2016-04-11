"""
This module contains the tools for handling YAML files and tags.
"""

import logging

import os
import re
import sys
import string

import configure
import yaml

from cli import exceptions
from cli import logger

LOG = logger.LOG

# Representer for Configuration object
yaml.SafeDumper.add_representer(
    configure.Configuration,
    lambda dumper, value:
    yaml.representer.BaseRepresenter.represent_mapping
    (dumper, u'tag:yaml.org,2002:map', value))


def _limit_chars(_string, length):
    length = int(length)
    if length < 0:
        raise exceptions.IRException('length to crop should be int, not ' +
                                     str(length))

    return _string[:length]


@configure.Configuration.add_constructor('limit_chars')
def _limit_chars_constructor(loader, node):
    """
    Usage:
        !limit_chars [<string>, <length>]
    Method returns first param cropped to <length> chars.
    """

    params = loader.construct_sequence(node)
    if len(params) != 2:
        raise exceptions.IRException(
            'limit_chars requires two params: string length')
    return _limit_chars(params[0], params[1])


class Random(yaml.YAMLObject):
    yaml_tag = u'!random'
    yaml_dumper = yaml.SafeDumper

    @classmethod
    def from_yaml(cls, loader, node):
        import random

        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(int(node.value)))


class Placeholder(yaml.YAMLObject):
    """ Raises 'IRPlaceholderException' when dumping Placeholder objects.

    Objects created by 'from_yaml' method are automatically added to the
    'placeholders_list' class variable so it'll be possible to add for each
    object the path to the file where it stored.
    """
    yaml_tag = u'!placeholder'
    yaml_dumper = yaml.SafeDumper

    # Refs for all Placeholder's objects
    placeholders_list = []

    def __init__(self, message):
        self.message = message
        self.file_path = None

    @classmethod
    def from_yaml(cls, loader, node):
        # Create & save references to Placeholder objects
        placeholder = Placeholder(str(node.start_mark))
        cls.placeholders_list.append(placeholder)
        return placeholder

    @classmethod
    def to_yaml(cls, dumper, node):
        message = re.sub("<string>", node.file_path, node.message)
        raise exceptions.IRPlaceholderException(message)


def load(settings_file, update_placeholders=True):
    """
    Loads and returns the content of a given YAML file as a dictionary

    :param settings_file: String represents a path to a YAML file
    :param update_placeholders: Whether to update Placeholder list or not in
    case of Placeholder tag is in the given YAML file
    :return: Dictionary containing the content the given YAML file
    """
    LOG.debug("Loading setting file: %s" % settings_file)
    if not os.path.exists(settings_file):
        raise exceptions.IRFileNotFoundException(settings_file)

    try:
        with open(settings_file) as f_obj:
            loaded_yml = yaml.load(f_obj)

        # Handling case of empty file
        if loaded_yml is None:
            return {}

        if update_placeholders:
            for placeholder in Placeholder.placeholders_list[::-1]:
                if placeholder.file_path is None:
                    placeholder.file_path = settings_file
                else:
                    break

        return loaded_yml

    except yaml.constructor.ConstructorError as e:
        raise exceptions.IRYAMLConstructorError(e, settings_file)


def _dict_flattener(ord_dict):
    """
    Converts ordinary dictionary into a flattened dictionary (all keys are
    in the root level, nested keys are separated by dots.

    Example:
      input:  {'key1': 'val1', 'key2': {'key21': 'val21', 'key22': 'val22'}}
      output: {'key1': 'val1', 'key2.key21': 'val21', 'key2.key22': 'val22'}


    :param ord_dict: Ordinary dictionary
    :return: Flattened dictionary
    """
    flattened_dict = {}

    def dict_builder(_dic, parent_key=''):
        for key, value in _dic.iteritems():
            if parent_key:
                key = parent_key + '.' + key

            if not isinstance(value, dict):
                flattened_dict[key] = value
            else:
                dict_builder(value, key)

    dict_builder(ord_dict)

    return flattened_dict


def _dict_inflator(flattened_dict):
    """
    Builds an ordinary dictionary from a flatten dictionary.
    (Reverse action to _dict_flattener function)

    Example:
      input:  {'key1': 'val1', 'key2.key21': 'val21', 'key2.key22': 'val22'}
      output: {'key1': 'val1', 'key2': {'key21': 'val21', 'key22': 'val22'}}

    :param flattened_dict: Flattened dictionary
    (Dictionary with root level keys only, nested keys separated by dots)
    :return: Ordinary dictionary
    """
    inflated_dict = {}

    def dict_builder(_dic, value, key, *keys):
        if not keys:
            _dic[key] = value
        else:
            _dic.setdefault(key, {})
            dict_builder(_dic[key], value, keys[0], *keys[1:])

    for flatten_key, flatten_value in flattened_dict.iteritems():
        dict_builder(inflated_dict, flatten_value, *flatten_key.split('.'))

    return inflated_dict


def _lookup_handler(flattened_dict):
    """
    Replaces all lookup patterns with the corresponding values

    Lookup pattern: "{{ !lookup key.sub_key }}'

    :param flattened_dict: Flattened dictionary
    (Dictionary with root level keys only, nested keys separated by dots)
    :return: Flattened dictionary without lookup patterns converted into
    corresponding values
    """
    lookups_list = []

    def get_most_nested_lookups(string_value):
        """
        Helper method that returns list of most nested lookups patterns from a
        given string (in case of lookup in lookup)

        :param string_value: String to search lookup patterns in it
        :return: List containing lookup patterns
        """
        parser = re.compile('\{\{\s*\!lookup\s*[\w.]*\s*\}\}')
        return parser.findall(string_value)

    for key, value in flattened_dict.iteritems():
        if isinstance(value, str) and get_most_nested_lookups(value):
            lookups_list.append(key)

    while lookups_list:
        changed = False

        for key in lookups_list:
            lookup_patterns = get_most_nested_lookups(flattened_dict[key])
            for lookup_pattern in lookup_patterns:
                lookup_key = re.search('(\w+\.?)+ *?\}\}', lookup_pattern)
                lookup_key = lookup_key.group(0).strip()[:-2].strip()

                if lookup_key in lookups_list:
                    continue
                elif lookup_key not in flattened_dict:
                    raise exceptions.IRKeyNotFoundException(lookup_key,
                                                            flattened_dict)

                flattened_dict[key] = re.sub(lookup_pattern,
                                             flattened_dict[lookup_key],
                                             flattened_dict[key], count=1)

                changed = True

            if not get_most_nested_lookups(flattened_dict[key]):
                lookups_list.remove(key)

        if not changed:
            raise exceptions.IRInfiniteLookupException(", ".join(
                lookups_list))


def replace_lookup(lookups_dict):
    """
    Replaces all lookup pattern in a given dictionary (lookups_dict) with
    the corresponding values

    :param lookups_dict: Ordinary dictionary (may contains lookup patterns)
    """
    flattened_dict = _dict_flattener(lookups_dict)
    _lookup_handler(flattened_dict)
    lookups_dict.clear()
    lookups_dict.update(_dict_inflator(flattened_dict))
