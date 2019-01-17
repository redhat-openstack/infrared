"""
This module is used to read command line arguments and validate them
according to the specification (spec) files.
"""

import argparse
import collections

import abc
import os
import re
import sys
from six.moves import configparser
from copy import deepcopy
from six import string_types
import yaml

from infrared.core.services import CoreServices
from infrared.core.utils import logger, exceptions, dict_utils

LOG = logger.LOG

# TODO(aopincar): Replace TYPES with supported types only (str, int, bool...)
BUILTINS = sys.modules[
    'builtins' if sys.version_info[0] == 3 else '__builtin__']

TYPES = dict((k, getattr(BUILTINS, k)) for k in vars(BUILTINS))

TYPES['suppress'] = argparse.SUPPRESS

OPTION_ARGPARSE_ATTRIBUTES = ['action', 'nargs', 'const', 'default', 'choices',
                              'required', 'help', 'metavar', 'type', 'version']

YAMLS_PLACEHODER = '__LISTYAMLS__'


class CliParser(object):
    """
    Allows to handle the CLI arguments.
    """

    def __init__(self):
        pass

    @classmethod
    def create_parser(cls, spec, subparser):
        parser_dict = spec.spec_helper.spec_dict

        # process subparsers
        subparsers = parser_dict.get('subparsers', {})
        if subparsers:
            dest_path = 'subcommand'

            for subparser_name, subparser_dict in parser_dict.get(
                    'subparsers', {}).items():
                cmd_parser = subparser.add_parser(
                    subparser_name,
                    help=subparser_dict.get(
                        'help', subparser_dict.get('description', '')),
                    description=subparser_dict.get(
                        'description', subparser_dict.get('help', '')),
                    formatter_class=parser_dict.get(
                        'formatter_class', argparse.RawTextHelpFormatter))

                cls._add_groups(
                    spec,
                    cmd_parser,
                    subparser_name,
                    subparser_dict,
                    path_prefix=dest_path)

        # cls._add_groups(spec, arg_parser, spec.app_name, parser_dict)
        return subparsers

    @classmethod
    def parse_cli_input(cls, arg_parser, args=None):
        """

        :param arg_parser: argparse object
        :param args: replace sys.argv[1:]
        :return: dict. Parsed CLI input
        """

        parse_args, unknown_args = arg_parser.parse_known_args(args)
        # todo(obaranov) Pass all the unknown arguments to the ansible
        # For now just raise exception
        if unknown_args:
            raise exceptions.IRUnrecognizedOptionsException(unknown_args)

        parse_args = parse_args.__dict__

        # move sub commands to the nested dicts
        result = collections.defaultdict(dict)
        expr = '^(?P<subcmd_name>subcommand)+(?P<arg_name>.*)$$'
        for arg, value in parse_args.items():
            if value is None:
                continue
            match = re.search(expr, arg)
            if match and match.groupdict().get('subcmd_name', None) \
                    and not match.groupdict().get('arg_name', None):
                # create empty nested dict for subcommands
                if value not in result:
                    result[value] = {}
            if match and match.groupdict().get('arg_name', None):
                # we have subcommand. put it as nested dict
                arg_name = match.group('arg_name')
                cmd_name = match.group('subcmd_name')
                sub_name = parse_args[cmd_name]
                result[sub_name][arg_name] = value

        return result

    @classmethod
    def _add_groups(cls, spec, arg_parser, parser_name, parser_data,
                    path_prefix=''):
        """Adds groups to the parser.

        This will group argument in HELP MESSAGE according to specifications.
        """
        options = []
        # add parser groups
        for grp_dict in parser_data.get('groups', []):
            group = arg_parser.add_argument_group(grp_dict['title'])
            # add options to the group
            for opt_name, opt_dict in grp_dict.get('options', {}).items():
                options.append(
                    cls._add_argument(spec, parser_name,
                                      group, opt_name, opt_dict, path_prefix))
        # add flat options (outside groups)
        for opt_name, opt_dict in parser_data.get('options', {}).items():
            options.append(
                cls._add_argument(spec, parser_name,
                                  arg_parser, opt_name, opt_dict, path_prefix))

        return options

    @classmethod
    def _add_argument(cls, spec, subparser, group, option_name, option_data,
                      path_prefix=''):
        """
        Adds argument to the group.
        """
        opt_args = []
        opt_kwargs = {}
        if 'short' in option_data:
            opt_args.append('-{}'.format(option_data['short']))
        opt_args.append('--{}'.format(option_name))

        # add prefix to ensure we can group subcommand arguments later
        opt_kwargs['dest'] = option_data.get(
            'dest', path_prefix + option_name)
        if 'type' in option_data:
            opt_kwargs['type'] = TYPES.get(option_data['type'])
            if opt_kwargs['type'] is None \
                    and option_data['type'] not in COMPLEX_TYPES:
                raise exceptions.IRUnsupportedSpecOptionType(
                    "Unsupported type '{}' of spec's option '{}'".format(
                        option_data['type'], option_name))

        for option_key in OPTION_ARGPARSE_ATTRIBUTES:
            if option_key != 'type' and option_key in option_data:
                opt_kwargs[option_key] = option_data[option_key]
        # set correct metavar to have correct name in the usage statement
        if 'metavar' not in opt_kwargs and opt_kwargs.get(
                'action', None) not in ['count', 'help', 'store_true']:
            opt_kwargs['metavar'] = option_name.upper()

        # resolve custom action
        if 'action' in opt_kwargs and opt_kwargs['action'] in ACTIONS:
            opt_kwargs['action'] = ACTIONS[opt_kwargs['action']]

        # update help if required.
        if 'help' not in opt_kwargs:
            opt_kwargs['help'] = ''

        # print default values to the help
        if opt_kwargs.get('default', None) is not None:
            opt_kwargs['help'] = \
                opt_kwargs['help'].rstrip() + \
                "\nDefault value: '{}'.".format(opt_kwargs['default'])

        # print length value to the help
        if 'length' in option_data:
            opt_kwargs['help'] += "\nMaximum variable length: '{}'.".format(
                option_data['length'])

        # print minimum value to the help
        if 'minimum' in option_data:
            opt_kwargs['help'] += "\nMinimum value: '{}'.".format(
                option_data['minimum'])

        # print maximum value to the help
        if 'maximum' in option_data:
            opt_kwargs['help'] += "\nMaximum value: '{}'.".format(
                option_data['maximum'])

        # print silent args to the help
        if option_data.get('silent', None):
            opt_kwargs['help'] += "\nWhen this option is set the following " \
                                  "options are not required: '{}'.".format(
                option_data['silent'])
        # print whether the option is required into help
        if opt_kwargs.get('required', None):
            opt_kwargs['help'] += "\nThis argument is required."

        # put allowed values to the help.
        allowed_values = opt_kwargs.get('choices', None)

        if 'type' in option_data:
            if option_data['type'] in COMPLEX_TYPES:
                complex_action = COMPLEX_TYPES.get(option_data['type'], None)
                if hasattr(complex_action, 'VALUES_AUTO_PROPAGATION') and \
                        complex_action.VALUES_AUTO_PROPAGATION:
                    complex_action = complex_action(
                        option_name,
                        (spec.vars, spec.defaults, spec.plugin_path),
                        subparser,
                        option_data)
                    allowed_values = \
                        complex_action.get_allowed_values()

            if option_data['type'] == 'Flag':
                opt_kwargs['action'] = 'store_true'
                opt_kwargs.pop('type', None)
                opt_kwargs.pop('metavar', None)

        if allowed_values:
            opt_kwargs['help'] += "\nAllowed values: {}.".format(
                allowed_values)
        elif YAMLS_PLACEHODER in opt_kwargs['help']:
            yaml_set = set()
            for dirname in (spec.vars, spec.defaults):
                option_dir = os.path.join(dirname, *option_name.split('-'))
                if not os.path.exists(option_dir):
                    continue
                yaml_files = [os.path.splitext(yml)[0]
                              for yml in os.listdir(option_dir)
                              if yml.endswith('.yml')]
                # yaml_files.sort()
                # set union operator
                yaml_set |= set(yaml_files)

            # convert set back to list
            opt_kwargs['help'] = opt_kwargs['help'].replace(
                YAMLS_PLACEHODER, "Available values: {}".
                format(list(yaml_set)))

        # update help
        option_data['help'] = opt_kwargs.get('help', '')

        # pop default
        result = deepcopy(opt_kwargs)
        if not any(arg in sys.argv for arg in ['-h', '--help']):
            opt_kwargs.pop('default', None)
            opt_kwargs['default'] = argparse.SUPPRESS
            opt_kwargs.pop('required', None)

        group.add_argument(*opt_args, **opt_kwargs)
        return result


# custom argparse actions
class ReadAnswersAction(argparse.Action):
    """Custom action to read input from answers file into argparse object. """

    def __call__(self, parser, namespace, values, option_string=None):
        # reading file
        _config = configparser.ConfigParser()
        with open(values) as fd:
            _config.readfp(fd)
        # todo(obaranov) add different file types loaders
        res_dict = {}
        # load only section for a given subcommand
        # todo(obaranov) consider resolving that in more intelligent way
        progs = parser.prog.split()
        subcommand = progs[-1]

        if subcommand in _config._sections:
            for option, val in _config.items(subcommand):
                # todo(obaranov) checking if val is list (for extra-vars).
                # rework that check to be more beautiful later.
                if val.startswith('[') and val.endswith(']'):
                    val = eval(str(val))
                elif val == 'False':
                    val = False
                elif val == 'True':
                    val = True
                res_dict[option] = val
            res_dict.pop('__name__', None)
        # saving
        setattr(namespace, self.dest, res_dict)


class GenerateAnswersAction(argparse._StoreAction):
    """Stub action for answers fiele generation. """
    pass


# Standard complex types
class ComplexType(object):
    """
    Base complex type.

    Complex accept additional input arguments beside the argument value
    """
    # specifies if complex type should be nested to the settings
    is_nested = True

    def __init__(self, arg_name,
                 settings_dirs,
                 sub_command_name,
                 spec_option):

        # FIXME(yfried): this should take plugin as input
        self.arg_name = arg_name
        self.sub_command_name = sub_command_name
        self.settings_dirs = settings_dirs
        self.spec_option = spec_option

    @abc.abstractmethod
    def resolve(self, value):
        """Resolves the value of the complex type.

        :return: the resulting complex type value.
        """

        """Gets the list of possible values for the complex type.

        Should be overridden in the subclasses.
        """
        return []


class Value(ComplexType):
    """The simple nested value option. """

    def resolve(self, value):
        """Returns the argument value. """
        return value


class Bool(Value):
    """The simple nested value option. """

    def resolve(self, value=True):
        """Returns the YAML boolean value. """
        value = yaml.load(str(value))
        if not isinstance(value, bool):
            raise exceptions.IRException("--{} expects boolean values".
                                         format(self.arg_name))
        return value


class Flag(Value):
    """The simple argument value option.

    This will always return True and will act as a flag which doesn't parse value
    """

    def resolve(self, value=False):
        return True


class AdditionalOptionsType(ComplexType):
    """Plumb ansible-playbook arguments to ansible executor

    This is a custom type to handle passing additional arguments to some part
    of infrared.

    Format should be --additional-args option1=value1;option2=value2
    """

    ARG_SEPARATOR = ';'
    # ansible args should not be put into the settings file
    is_nested = False

    def resolve(self, value):
        arguments = value.split(AdditionalOptionsType.ARG_SEPARATOR)
        res = []
        for argument in arguments:
            argument = argument.strip()
            if '=' in argument:
                name, value = argument.split('=', 1)
                res.append("--" + name)
                res.append(value)
            else:
                res.append("--" + argument)

        return res


class Inventory(ComplexType):
    """Accepts an Ansible Inventory file as active workspace's inventory. """

    is_nested = False

    def resolve(self, value):
        """Set active workspace's inventory

        Assumes active workspace exists, as ComplexType objects are resolved
        after workspace is verified.

        Calls workspace.inventory setter. See source for more information.

        :param value: path to inventory file.
        """
        CoreServices.workspace_manager()\
            .get_active_workspace().inventory = value


class KeyValueList(ComplexType):
    """Accept a key-value like list.

    Format should be in one of two acceptable styles: New / Old
    Default style: --options="option1:value1,option2:value2"

    :returns: A flat dict: ex. {'option1': 'value1', 'option2': 'value2'}
    """

    new_format = 'NodeA:1,NodeB:2...'

    re_pattern = \
        '([\w\-\.]+{assign}[\w\-\.\:/]+\{separate})*([\w\-\.]+{assign}[\w\-\.\:/]+)'
    regex_formats = dict(
        default_style=dict(assign=':', separate=','),
    )

    def resolve(self, value):
        result_dict = {}
        for style, data in self.regex_formats.items():
            p = self.re_pattern.format(
                assign=data['assign'], separate=data['separate'])
            match_obj = re.match(pattern=p, string=value)

            if match_obj is None:
                continue

            match_str = match_obj.group(0)
            if match_str is not value:
                continue

            if style is 'old_style':
                LOG.warning("This format of KeyValue value is deprecated, "
                            "Please enter values in the following "
                            "format: {}".format(self.new_format))

            result_dict = dict(pair.split(data['assign'], 1)
                               for pair in value.split(data['separate']))
            break

        else:
            raise exceptions.IRKeyValueListException(
                "'{}' is a wrong format for '{}' argument type. Please enter "
                "values in the following format: {}".format(
                    value, self.__class__.__name__, self.new_format))

        return result_dict


class NestedBase(object):
    """Base Nested type"""

    def _resolve(self, value, skip_nested_split=False):
        if isinstance(value, string_types):
            value = value.split(',')

        results_dict = {}
        for item in value:
            data = item.strip().split('=')
            if len(data) > 2:
                raise ValueError(
                    'Wrong number of arguments are provided {}'.format(data))
            key, _value = data
            if skip_nested_split:
                dict_utils.dict_insert(results_dict, _value, key)
            else:
                dict_utils.dict_insert(results_dict, _value, *key.split('.'))
        return results_dict


class Dict(ComplexType, NestedBase):
    """Returns a dict from a dict-like string / list of strings"""

    def resolve(self, value):
        return self._resolve(value, skip_nested_split=True)


class NestedDict(ComplexType, NestedBase):
    """Returns a dict from a dict-like string / list of strings

    For example:
      "section.option=value"
        -> {'section': {'option': 'value'}}

      "section1.option1=value1,section1.option2=value2"
        -> {'section1': {'option1': 'value1', 'option2': 'value2'}}

      ["section1.option1=value1", "section1.option2=value2"]
        -> {'section1': {'option1': 'value1', 'option2': 'value2'}}
    """

    def resolve(self, value):
        return self._resolve(value)

IniType = NestedDict


class NestedList(ComplexType, NestedBase):
    """Returns a list from a dict-like string / list of strings

    For example:
      "section.option=value"
        -> [{'section': {'option': 'value'}}]

      "section1.option1=value1,section1.option2=value2"
        -> [{'section1': {'option1': 'value1', 'option2': 'value2'}}]

      ["section1.option1=value1", "section1.option2=value2"]
        -> [{'section1': {'option1': 'value1'}},
            {'section1': {'option2': 'value2'}}]
    """

    def resolve(self, value):
        if isinstance(value, string_types):
            return [self._resolve(value)]
        else:
            return [self._resolve(v) for v in value]


class ListValue(ComplexType):
    """Accept a list as string input.

    Format should be --options="option1,option2,option3"

    Resulting vars-dict entry will look like:
    options:
        - option1
        - option2
        - option3
    """
    ARG_SEPARATOR = ','

    def resolve(self, value):
        return value.split(self.ARG_SEPARATOR)


class FileType(ComplexType):
    """Transforms a value to the absolute path"""

    # specifies whather the yaml files should be searched
    SEARCH_YAML = True

    def get_check_locations(self, value):
        """Get the file names of possible location of the file"""
        return [value,
                os.path.join(os.path.join(*self.arg_name.split('-')), value)]

    @staticmethod
    def validate(file_path):
        """Validate path"""
        return os.path.isfile(os.path.abspath(file_path))

    def resolve(self, value):
        pathes = self.get_check_locations(value)
        # check also for files with yml extension
        if self.SEARCH_YAML:
            pathes.extend(
                [path + '.yml' for path in pathes
                 if not path.endswith('.yml')])

        target_file = next(
            (file_path for file_path in pathes
             if self.__class__.validate(file_path)),
            None)

        if target_file is None:
            raise exceptions.IRFileNotFoundException(pathes)

        return os.path.abspath(target_file)


class ListOfFileNames(ComplexType):
    """ Represents List of file names for specific path

        It support value auto propagation, based on
        plugin_path and spec_option['lookup_dir'])
    """

    ARG_SEPARATOR = ','
    VALUES_AUTO_PROPAGATION = True

    @property
    def plugin_path(self):
        return self.settings_dirs[2]

    @property
    def lookup_dir(self):
        return self.spec_option['lookup_dir']

    @property
    def files_path(self):
        return os.path.join(self.plugin_path, self.lookup_dir)

    def get_allowed_values(self):
        """ Generate list of file names in specific path"""
        result = list(map((lambda name: os.path.splitext(name)[0]),
                          os.listdir(self.files_path)))
        result.sort()
        return result

    def validate(self, value):
        """Validate if value is allowed"""
        allowed_values = self.get_allowed_values()
        if value not in allowed_values:
            raise exceptions.IRFileNotFoundException(self.files_path)

    def resolve(self, value):
        result = value.split(self.ARG_SEPARATOR)
        for arg in result:
            self.validate(arg)
        return result


class VarFileType(FileType):
    """Represents the file on a disk.

    Looks for a file in the following locations:
        * in the given file_name location. Can be absolute or relative
        * arg/name/file_name
        * plugin_dir/defaults/arg/name/file_name
        * plugin_dir/vars/arg/name/file_name
    """

    @property
    def vars_dir(self):
        return self.settings_dirs[0]

    @property
    def defaults_dir(self):
        return self.settings_dirs[1]

    def get_check_locations(self, value):
        pathes = [
            os.path.join(
                os.path.join(self.vars_dir, *self.arg_name.split('-')),
                value),
            os.path.join(
                os.path.join(self.defaults_dir, *self.arg_name.split('-')),
                value)
        ]

        # check also for files with yml extension
        result = super(VarFileType, self).get_check_locations(value)
        result.extend(pathes)
        return result


class VarDirType(VarFileType):
    """Represents the directory on a disk.

    Looks for a file in the following locations:
        * in the given file_name location. Can be absolute or relative
        * arg/name/<value>/
        * plugin_dir/vars/arg/name/<value>/
        * plugin_dir/defaults/arg/name/<value>/
    """
    SEARCH_YAML = False

    @staticmethod
    def validate(file_path):
        """Validate path"""
        return os.path.isdir(os.path.abspath(file_path))


class ListFileType(VarFileType):
    """
    The list of var files. Files names should be separated
    by the comma:

        file1,file2,dir/file3
    """

    ARG_SEPARATOR = ','

    def resolve(self, value):
        return [super(ListFileType, self).resolve(file_name.strip())
                for file_name in value.split(self.ARG_SEPARATOR)]


class TopologyFileType(VarFileType):
    """
    Looks for a topology file in following locations:
        * relative path (./path)
        * abs path ($PWD/path)
        * <plugin_root>/vars
        * <plugin_root>/defaults
    """
    ARG_SEPARATOR = ','
    TOPOLOGY_SEPARATOR = ':'

    def resolve(self, value):

        return dict((super(TopologyFileType, self).resolve(
            file_name.split(self.TOPOLOGY_SEPARATOR)[0]),
            int(file_name.split(self.TOPOLOGY_SEPARATOR)[1]))
            for file_name in value.split(self.ARG_SEPARATOR))


# register custom actions
ACTIONS = {
    'read-answers': ReadAnswersAction,
    'generate-answers': GenerateAnswersAction
}

# register complex Types. See ComplexType to implement new types
COMPLEX_TYPES = {
    'Value': Value,
    'Bool': Bool,
    'Flag': Flag,
    'Dict': Dict,
    'Inventory': Inventory,
    'KeyValueList': KeyValueList,
    'AdditionalArgs': AdditionalOptionsType,
    'ListValue': ListValue,
    'IniType': IniType,
    'NestedDict': NestedDict,
    'NestedList': NestedList,
    'FileValue': FileType,
    'VarFile': VarFileType,
    'VarDir': VarDirType,
    'ListOfVarFiles': ListFileType,
    'ListOfTopologyFiles': TopologyFileType,
    'ListOfFileNames': ListOfFileNames
}
