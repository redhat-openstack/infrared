"""
This module contains the tools for handling YAML files and tags.
"""

import logging
import re
import sys

import yaml

from cli import exceptions
from cli import logger

LOG = logger.LOG


class Lookup(yaml.YAMLObject):
    yaml_tag = u'!lookup'
    yaml_dumper = yaml.SafeDumper

    settings = None

    def __init__(self, key, old_style_lookup=False):
        self.key = key
        if old_style_lookup:
            self.convert_old_style_lookup()
        self.handling_nested_lookups = False

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

        my_iter = settings_dic.iteritems() if isinstance(settings_dic, dict)\
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
    def handle_nested_lookup(cls, node):
        """ handles lookup to lookup (nested lookup scenario)

        load and dump 'settings' again and again until all lookups strings
        are converted into Lookup objects
        """

        # because there is a call to 'yaml.safe_dump' which call to this
        # method, the 'handling_nested_lookups' flag is being set & unset to
        # prevent infinite loop between the method
        node.handling_nested_lookups = True

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

        node.handling_nested_lookups = False

    @classmethod
    def from_yaml(cls, loader, node):
        return Lookup(loader.construct_scalar(node), old_style_lookup=True)

    @classmethod
    def to_yaml(cls, dumper, node):
        if not node.handling_nested_lookups:
            node.handle_nested_lookup(node)

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
