"""
This module contains the tools for handling YAML files and tags.
"""
import os
import random
import re
import string

import yaml

from cli import exceptions
from cli import logger

LOG = logger.LOG
LOOKUP_REGEX = '\{\{\s*\!lookup\s*[\w.]*\s*\}\}'
LOOKUP_KEY_REGEX = '(\w+\.?)+ *?\}\}'


class Random(yaml.YAMLObject):
    """
    Class for '!random' YAML tag
    """
    yaml_tag = u'!random'
    yaml_dumper = yaml.SafeDumper

    @classmethod
    def from_yaml(cls, loader, node):
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
            raise exceptions.IREmptySettingsFile(settings_file)

        if update_placeholders:
            for placeholder in Placeholder.placeholders_list[::-1]:
                if placeholder.file_path is None:
                    placeholder.file_path = settings_file
                else:
                    break

        return loaded_yml

    except yaml.constructor.ConstructorError as e:
        raise exceptions.IRYAMLConstructorError(e, settings_file)


# TODO(aopincar): Remove use in inner function
def replace_lookup(lookups_dict):
    """
    Replaces all lookup pattern in a given dictionary (lookups_dict) with
    the corresponding values

    :param lookups_dict: Dictionary with data to replace
    """
    def yaml_walk(yaml_content, key_path=None):
        an_iter = enumerate(yaml_content) if isinstance(yaml_content, list) \
            else yaml_content.iteritems()

        for idx_key, value in an_iter:
            if hasattr(value, '__iter__'):
                if key_path is None:
                    next_key = str(idx_key)
                else:
                    next_key = key_path + '.' + str(idx_key)
                yaml_walk(value, next_key)
            elif isinstance(value, str):
                yaml_content[idx_key] = _lookup_handler(
                    value, lookups_dict, key_path)

    yaml_walk(lookups_dict)


# TODO(aopincar): Refactor this method (to be recursive only - no while & for)
def _lookup_handler(lookup_string, data_dict, key_path, visited=None):
    """
    Lookups handling mechanism

    :param lookup_string: string containing the lookup pattern to be handled
    :param data_dict: The complete data dictionary
    :param key_path: Path to the value's key we currently handling
    :param visited: List of already visited keys (infinite loop indicator)
    :return:
    """
    if visited is None:
        visited = []
    visited.append(key_path)

    while True:
        # Get deepest lookups
        lookups = re.compile(LOOKUP_REGEX).findall(lookup_string)
        if not lookups:
            break

        for lookup in lookups:
            lookup_key = re.search(LOOKUP_KEY_REGEX, lookup)
            lookup_key = lookup_key.group(0).strip()[:-2].strip()

            if lookup_key in visited:
                raise exceptions.IRInfiniteLookupException(", ".join(visited))

            new_value = _lookup_handler(dict_get(data_dict, lookup_key),
                                        data_dict, lookup_key, visited)

            lookup_string = re.sub(lookup, new_value, lookup_string, count=1)

    return lookup_string


# TODO(aopincar): Remove use in inner function
def dict_get(dic, key):
    """
    Gets the value of a nested key in a dictionary

    :param dic: Dictionary containing the needed data
    :param key: String representing full key path (Example: 'key.sub1.sub2')
    :return: Value of a given key in the dictionary
    """
    def _dict_get(_dic, current_key, *keys):
        try:
            if not keys:
                return _dic[current_key]

            return _dict_get(_dic[current_key], *keys)
        except KeyError:
            raise exceptions.IRKeyNotFoundException(key, dic)

    return _dict_get(dic, *key.split('.'))
