"""
This module provide some general helper methods
"""

import os

import configure

import cli.yamls
from cli import exceptions
from cli import logger

LOG = logger.LOG


def dict_insert(dic, val, key, *keys):
    """insert a value of a nested key into a dictionary

    to insert value for a nested key, all ancestor keys should be given as
    method's arguments

    example:
      dict_insert({}, 'val', 'key1.key2'.split('.'))

    :param dic: a dictionary object to insert the nested key value into
    :param val: a value to insert to the given dictionary
    :param key: first key in a chain of key that will store the value
    :param keys: sub keys in the keys chain
    """
    if not keys:
        if key in dic and isinstance(val, dict):
            dict_merge(dic[key], val)
        else:
            dic[key] = val
        return

    dict_insert(dic.setdefault(key, {}), val, *keys)


class ConflictResolver(object):
    """
    Resolves conflicts while merging dicts.
    """

    @staticmethod
    def none_resolver(first, second, key):
        """
        Replaces value in first dict only if it is None.
        Appends second value into the first in type is list.
        """

        # tyr to merge lists first
        if isinstance(first[key], list):
            if isinstance(second[key], list):
                first[key].extend(second[key])
            elif second[key] is not None:
                first[key].append(second[key])

        if key not in first or first[key] is None:
            first[key] = second[key]

    @staticmethod
    def greedy_resolver(first, second, key):
        """
        Replace always first with the value from second
        """
        first[key] = second[key]


def dict_merge(first, second,
               conflict_resolver=ConflictResolver.greedy_resolver):
    """Merge `second` dict into `first`.

    :param first: Modified dict
    :param second: Modifier dict
    :param conflict_resolver: Function that resolves a merge between 2 values
        when one of them isn't a dict
    """
    for key in second:
        if key in first:
            if isinstance(first[key], dict) and isinstance(second[key], dict):
                dict_merge(first[key], second[key],
                           conflict_resolver=conflict_resolver)
            else:
                # replace first value with the value from second
                conflict_resolver(first, second, key)
        else:
            first[key] = second[key]


def search_tree(needle, haystack, _res=None):
    """Find all values of key `needle` inside a nested dict tree `haystack`.

    :param haystack: nested dict tree to search
    :param needle: key name to search for
    :param _res: helper argument holding return value for internal recursion
    :return: list. All values of key `needle` in tree `haystack`. Order is not
        guaranteed.
    """
    if _res is None:
        _res = []
    if needle in haystack:
        _res.append(haystack[needle])
    for key, value in haystack.iteritems():
        if isinstance(value, dict):
            search_tree(needle, value, _res)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    search_tree(needle, item, _res)
    return _res


def update_settings(settings, file_path):
    """merge settings in 'file_path' with 'settings'

    :param settings: settings to be merge with (configure.Configuration)
    :param file_path: path to file with settings to be merged
    :return: merged settings
    """
    loaded_dict = cli.yamls.load(file_path, True)
    dict_merge(settings, loaded_dict)
    return settings


def merge_extra_vars(settings, extra_vars):
    """ Merging 'extra-vars' into 'settings'

    :param settings: configure.Configuration objects with settings
    :param extra_vars: list of extra-vars
    """
    for extra_var in extra_vars or []:
        if extra_var.startswith('@'):
            if not len(extra_var[1:]):
                raise exceptions.IRExtraVarsException(extra_var)
            settings_file = normalize_file(extra_var[1:])
            settings = update_settings(settings, settings_file)

        else:
            if '=' not in extra_var:
                raise exceptions.IRExtraVarsException(extra_var)
            key, value = extra_var.split("=")
            dict_insert(settings, value, *key.split("."))

    return settings


def generate_settings(settings_files):
    """ Generates one settings object (configure.Configuration) by merging all
    files in settings_files

    :param settings_files: list of paths to settings files
    :return: Configuration object with merging results of all settings
    files and extra-vars
    """
    settings = configure.Configuration.from_dict({})

    for settings_file in settings_files:
        settings = update_settings(settings, settings_file)

    return settings


# todo: convert into a file object to be consumed by argparse
def normalize_file(file_path):
    """Return a normalized absolutized version of a file

    :param file_path: path to file to be normalized
    :return: normalized path of a file
    :raise: IRFileNotFoundException if the file doesn't exist
    """
    if not os.path.isabs(file_path):
        abspath = os.path.abspath(file_path)
        LOG.debug(
            'Setting the absolute path of "%s" to: "%s"'
            % (file_path, abspath)
        )
        file_path = abspath

    if not os.path.exists(file_path):
        raise exceptions.IRFileNotFoundException(file_path)

    return file_path


def load_yaml(filename, *search_paths):
    """Find YAML file. search default path first.

    :param filename: path to file
    :param search_first: default path to search first
    :returns: dict. loaded YAML file.
    """
    path = None
    searched_files = []
    files_to_search = map(
        lambda search_path: os.path.join(search_path, filename), search_paths)
    # append file name to verify absolute path by default
    files_to_search.append(filename)

    for filename in files_to_search:
        searched_files.append(os.path.abspath(filename))
        if os.path.exists(filename):
            path = os.path.abspath(filename)
            break

    if path is not None:
        print("Loading YAML file: %s" % path)
        return cli.yamls.load(path)
    else:
        raise exceptions.IRFileNotFoundException(
            file_path=searched_files)


ENV_VAR_NAME = "IR_CONFIG"
IR_CONF_FILE = 'infrared.cfg'
USER_PATH = os.path.expanduser('~/.' + IR_CONF_FILE)
SYSTEM_PATH = os.path.join('/etc/infrared', IR_CONF_FILE)
INFRARED_DIR_ENV_VAR = 'IR_SETTINGS'
