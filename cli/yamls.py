"""
This module contains the tools for handling YAML files and tags.
"""

import logging
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


def random_generator(size=32, chars=string.ascii_lowercase + string.digits):
    import random

    return ''.join(random.choice(chars) for _ in range(size))


@configure.Configuration.add_constructor('join')
def _join_constructor(loader, node):
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])


@configure.Configuration.add_constructor('random')
def _random_constructor(loader, node):
    """
    usage:
        !random <length>
    returns a random string of <length> characters
    """

    num_chars = loader.construct_scalar(node)
    return random_generator(int(num_chars))


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


@configure.Configuration.add_constructor('env')
def _env_constructor(loader, node):
    """
    usage:
        !env <var-name>
        !env [<var-name>, [default]]
        !env [<var-name>, [default], [length]]
    returns value for the environment var-name
    default may be specified by passing a second parameter in a list
    length is maximum length of output (croped to that length)
    """

    import os
    # scalar node or string has no defaults,
    # raise IRUndefinedEnvironmentVariableExcption if absent
    if isinstance(node, yaml.nodes.ScalarNode):
        try:
            return os.environ[loader.construct_scalar(node)]
        except KeyError:
            raise exceptions.IRUndefinedEnvironmentVariableExcption(node.value)

    seq = loader.construct_sequence(node)
    var = seq[0]
    if len(seq) >= 2:
        ret = os.getenv(var, seq[1])  # second item is default val

        # third item is max. length
        if len(seq) == 3:
            ret = _limit_chars(ret, seq[2])
        return ret

    return os.environ[var]


class Lookup(yaml.YAMLObject):
    yaml_tag = u'!lookup'
    yaml_dumper = yaml.SafeDumper

    settings = None
    handling_nested_lookups = False

    def __init__(self, key, old_style_lookup=False):
        self.key = key
        if old_style_lookup:
            self.convert_old_style_lookup()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.key)

    def convert_old_style_lookup(self):
        self.key = '{{!lookup %s}}' % self.key

        parser = re.compile('\[\s*\!lookup\s*[\w.]*\s*\]')
        lookups = parser.findall(self.key)

        for lookup in lookups:
            self.key = self.key.replace(lookup, '.{{%s}}' % lookup[1:-1])

    def replace_lookup(self):
        """
        Replace any !lookup with the corresponding value from settings table
        """
        while True:
            parser = re.compile('\{\{\s*\!lookup\s*[\w.]*\s*\}\}')
            lookups = parser.findall(self.key)

            if not lookups:
                break

            for a_lookup in lookups:
                lookup_key = re.search('(\w+\.?)+ *?\}\}', a_lookup)
                lookup_key = lookup_key.group(0).strip()[:-2].strip()
                lookup_value = self.dict_lookup(lookup_key.split("."))

                if isinstance(lookup_value, Lookup):
                    return

                lookup_value = str(lookup_value)

                self.key = re.sub('\{\{\s*\!lookup\s*[\w.]*\s*\}\}',
                                  lookup_value, self.key, count=1)

    def dict_lookup(self, keys, dic=None):
        """ Returns the value of a given key from the settings class variable

        to get the value of a nested key, all ancestor keys should be given as
        method's arguments

        example:
          if one want to get the value of 'key3' in:
            {'key1': {'key2': {'key3': 'val1'}}}

          dict_lookup(['key1', 'key2', 'key3'])
        return value:
          'val1'

        :param keys: list with keys describing the path to the target key
        :param dic: mapping object holds settings. (self.settings by default)

        :return: value of the target key
        """
        if LOG.getEffectiveLevel() <= logging.DEBUG:
            calling_method_name = sys._getframe().f_back.f_code.co_name
            current_method_name = sys._getframe().f_code.co_name
            if current_method_name != calling_method_name:
                LOG.debug(
                    'looking up the value of "{keys}"'.format(
                        keys=".".join(keys)))

        if dic is None:
            dic = self.settings

        key = keys.pop(0)

        if key not in dic:
            if isinstance(key, str) and key.isdigit():
                key = int(key)
            elif isinstance(key, int):
                key = str(key)

        try:
            if keys:
                return self.dict_lookup(keys, dic[key])

            value = dic[key]
        except KeyError:
            raise exceptions.IRKeyNotFoundException(key, dic)

        LOG.debug('value has been found: "{value}"'.format(value=value))
        return value

    @classmethod
    def in_string_lookup(cls, settings_dic=None):
        """ convert strings containing '!lookup' in them, and didn't already
        converted into Lookup objects.
        (in case when the strings don't start with '!lookup')

        :param settings_dic: a settings dictionary to search and convert
        lookup from
        """

        if settings_dic is None:
            settings_dic = cls.settings

        my_iter = settings_dic.iteritems() if isinstance(settings_dic, dict) \
            else enumerate(settings_dic)

        for idx_key, value in my_iter:
            if isinstance(value, dict):
                cls.in_string_lookup(settings_dic[idx_key])
            elif isinstance(value, list):
                cls.in_string_lookup(value)
            elif isinstance(value, str):
                parser = re.compile('\{\{\s*\!lookup\s*[\w.]*\s*\}\}')
                lookups = parser.findall(value)

                if lookups:
                    settings_dic[idx_key] = cls(value)

    @classmethod
    def handle_nested_lookup(cls):
        """ handles lookup to lookup (nested lookup scenario)

        load and dump 'settings' again and again until all lookups strings
        are converted into Lookup objects
        """

        # because there is a call to 'yaml.safe_dump' which call to this
        # method, the 'handling_nested_lookups' flag is being set & unset to
        # prevent infinite loop between the method
        cls.handling_nested_lookups = True

        first_dump = True
        settings = cls.settings

        while True:
            if not first_dump:
                cls.settings = settings
                settings = yaml.load(output)

            cls.in_string_lookup()
            output = yaml.safe_dump(cls.settings, default_flow_style=False)

            if first_dump:
                first_dump = False
                continue

            if not cmp(settings, cls.settings):
                break

        cls.handling_nested_lookups = False

    @classmethod
    def from_yaml(cls, loader, node):
        return Lookup(loader.construct_scalar(node), old_style_lookup=True)

    @classmethod
    def to_yaml(cls, dumper, node):
        if not cls.handling_nested_lookups:
            cls.handle_nested_lookup()

        if node.settings:
            node.replace_lookup()

        return dumper.represent_data("%s" % node.key)


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
