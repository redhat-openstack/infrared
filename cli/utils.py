"""
This module provide some general helper methods
"""

import cli.yamls
import configure
import os
import yaml
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
        Replaces value in first dict only if it null
        """

        # tyr to merge lists first
        if isinstance(first[key], list):
            if isinstance(second[key], list):
                first[key].extend(second[key])
            elif second[key] is not None:
                first[key].append(first[key])

        if key not in first or first[key] is None:
            first[key] = second[key]


def dict_merge(first, second, path=None,
               conflict_resolver=ConflictResolver.none_resolver):
    """ Given two dict objects, this function returns
    a dict that is the result of merging them into one.
    """
    if path is None:
        path = []
    for key in second:
        if key in first:
            if isinstance(first[key], dict) and isinstance(second[key], dict):
                dict_merge(first[key], second[key], path + [str(key)])
            elif first[key] == second[key]:
                pass
            else:
                # replace first value with the value from second
                conflict_resolver(first, second, key)
        else:
            first[key] = second[key]
    return first


# TODO: remove "settings" references in project
def validate_settings_dir(settings_dir=None):
    """Checks & returns the full path to the settings dir.

    Path is set in the following priority:
    1. Method argument
    2. System environment variable

    :param settings_dir: path given as argument by a user
    :return: path to settings dir (str)
    :raise: IRFileNotFoundException: when the path to the settings dir doesn't
            exist
    """
    settings_dir = settings_dir or os.environ.get(INFRARED_DIR_ENV_VAR)

    if not os.path.exists(settings_dir):
        raise exceptions.IRFileNotFoundException(
            settings_dir,
            "Settings dir doesn't exist: ")

    return settings_dir


def update_settings(settings, file_path):
    """merge settings in 'file_path' with 'settings'

    :param settings: settings to be merge with (configure.Configuration)
    :param file_path: path to file with settings to be merged
    :return: merged settings
    """
    LOG.debug("Loading setting file: %s" % file_path)
    if not os.path.exists(file_path):
        raise exceptions.IRFileNotFoundException(file_path)

    try:
        loaded_file = configure.Configuration.from_file(file_path).configure()
        placeholders_list = cli.yamls.Placeholder.placeholders_list
        for placeholder in placeholders_list[::-1]:
            if placeholder.file_path is None:
                placeholder.file_path = file_path
            else:
                break
    except yaml.constructor.ConstructorError as e:
        raise exceptions.IRYAMLConstructorError(e, file_path)

    settings = settings.merge(loaded_file)

    return settings


def generate_settings(settings_files, extra_vars):
    """ Generates one settings object (configure.Configuration) by merging all
    files in settings file & extra-vars

    files in 'settings_files' are the first to be merged and after them the
    'extra_vars'

    :param settings_files: list of paths to settings files
    :param extra_vars: list of extra-vars
    :return: Configuration object with merging results of all settings
    files and extra-vars
    """
    settings = configure.Configuration.from_dict({})

    for settings_file in settings_files:
        settings = update_settings(settings, settings_file)

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


def string_to_list(value, separator=',', append_to_list=True):
    """
    Converts string to list.
    """
    if value.startswith('[') and value.endswith(']'):
        value = value[1:-1].split(separator)
    else:
        if append_to_list:
            value = [value, ]
    return value

ENV_VAR_NAME = "IR_CONFIG"
IR_CONF_FILE = 'infrared.cfg'
USER_PATH = os.path.expanduser('~/.' + IR_CONF_FILE)
SYSTEM_PATH = os.path.join('/etc/infrared', IR_CONF_FILE)
INFRARED_DIR_ENV_VAR = 'IR_SETTINGS'
