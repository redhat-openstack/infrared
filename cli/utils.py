"""
This module provide some general helper methods
"""

import os
import re

import configure
import yaml

import cli.yamls
import cli.conf
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
    settings_dir = settings_dir or os.environ.get(
        cli.conf.INFRARED_DIR_ENV_VAR)

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
            if placeholders_list[-1].file_path is None:
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

    for extra_var in extra_vars:
        if extra_var.startswith('@'):
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
