"""
This module is used to read command line arguments and validate them
according to the specification (spec) files.
"""

import argparse
import collections
import glob
import os
import re
import sys
import ConfigParser
import yaml
from copy import deepcopy

from infrared.core.utils import logger, utils, exceptions

LOG = logger.LOG

BUILTINS = sys.modules[
    'builtins' if sys.version_info.major == 3 else '__builtin__']
TYPES = {builtin: getattr(BUILTINS, builtin) for builtin in vars(BUILTINS)}
TYPES['suppress'] = argparse.SUPPRESS

OPTION_ARGPARSE_ATTRIBUTES = ['action', 'nargs', 'const', 'default', 'choices',
                              'required', 'help', 'metavar', 'type', 'version']


class CliParser(object):
    """
    Allows to handle the CLI arguments.
    """

    def __init__(self, parser):
        pass

    @classmethod
    def create_parser(cls, spec, subparsers=None):
        parser_dict = spec.spec_helper.spec_dict

        if subparsers is None:
            arg_parser = argparse.ArgumentParser(
                description=parser_dict.get('description', ''),
                formatter_class=parser_dict.get(
                    'formatter_class', argparse.RawTextHelpFormatter))
        else:
            arg_parser = subparsers.add_parser(
                spec.app_name,
                help=parser_dict.get('description', ''),
                formatter_class=parser_dict.get(
                    'formatter_class', argparse.RawTextHelpFormatter))

        cls._add_groups(spec, arg_parser, spec.app_name, parser_dict)

        # process subparsers
        subparsers = parser_dict.get('subparsers', {})
        if subparsers:
            dest_path = 'command0'
            arg_subparser = arg_parser.add_subparsers(
                dest=dest_path)

            for subparser_name, subparser_dict in parser_dict.get(
                    'subparsers', {}).items():
                cmd_parser = arg_subparser.add_parser(
                    subparser_name,
                    help=subparser_dict.get('help', ''),
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

        return arg_parser

    @classmethod
    def parse_args(cls, spec, arg_parser):
        parse_args, unrecognized = arg_parser.parse_known_args()
        parse_args = parse_args.__dict__

        # move sub commands to the nested dicts
        result = collections.defaultdict(dict)
        expr = '^(?P<subcmd_name>command[0-9])+(?P<arg_name>.*)$$'
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
            else:
                result[spec.app_name][arg] = value

        return result, CliParser._transform_unknown_args(unrecognized)

    @classmethod
    def _add_groups(cls, spec, arg_parser, parser_name, parser_data,
                    path_prefix=''):
        """
        Adds groups to the parser.
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
        if opt_kwargs.get('default', None):
            opt_kwargs['help'] += "\nDefault value: '{}'.".format(
                opt_kwargs['default'])

        # print silent args to the help
        if option_data.get('silent', None):
            opt_kwargs['help'] += "\nWhen this option is set the following " \
                                  "options are not required: '{}'.".format(
                option_data['silent'])
        # print whether the option is required into help
        if opt_kwargs.get('required', None):
            opt_kwargs['help'] += "\nThis argument is required."

        # put allowed values to the help.
        allowed_values = []
        if opt_kwargs.get('choices', None):
            allowed_values = opt_kwargs['choices']
        elif option_data.get('type', None) and \
                option_data['type'] in COMPLEX_TYPES:
            action = spec.create_custom_type(
                subparser,
                option_data['type'],
                option_name)

            allowed_values = action.get_allowed_values()

        if allowed_values:
            opt_kwargs['help'] += "\nAllowed values: {}.".format(
                allowed_values)

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

    @staticmethod
    def _transform_unknown_args(uargs):
        """
        Transforms the list of args to the dict
        """
        prefix_chars = ['-']
        result = {}
        skip_next = False
        for arg_index, arg in enumerate(uargs):
            if skip_next:
                skip_next = False
                continue
            if arg and arg[0] in prefix_chars:
                if arg and '=' in arg:
                    name, value = arg.split('=')
                else:
                    name = arg
                    # check if this is a flag or arg value separated with space
                    if arg_index < len(uargs) - 1:
                        if uargs[arg_index + 1][0] in prefix_chars:
                            value = True
                        else:
                            value = uargs[arg_index + 1]
                            skip_next = True
                    else:
                        # last flag
                        value = True
            else:
                name = arg
                value = True

            normal_name = name.lstrip("".join(prefix_chars))
            result[normal_name] = CliParser._transform_unknown_value(value)

        return result

    @staticmethod
    def _transform_unknown_value(value):
        if value in ['yes', 'true', 'True']:
            value = True
        elif value in ['no', 'false', 'False']:
            value = False

        return value


# custom argparse actions
class ReadConfigAction(argparse.Action):
    """
    Custom action to read configuration file and
    inject arguments into argparse from file
    """

    def __call__(self, parser, namespace, values, option_string=None):
        # reading file
        _config = ConfigParser.ConfigParser()
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


class GenerateConfigAction(argparse._StoreAction):
    """
    Placeholder to identify an action to generate
    config file with the default values
    """
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
                 app_name,
                 app_subfolder,
                 sub_command_name):
        self.arg_name = arg_name
        self.sub_command_name = sub_command_name
        self.app_name = app_name
        self.app_subfolder = app_subfolder
        self.settings_dirs = settings_dirs

    def resolve(self, value):
        """
        Resolves the value of the complex type.
        :return: the resulting complex type value.
        """
        raise NotImplemented()

    def get_allowed_values(self):
        """
        Gets the list of possible values for the complex type.

        Should be overridden in the subclasses.
        """
        return []

    def get_file_locations(self):
        """
        Get the possible locations (folders) where the
        yaml files can be stored.
        """

        search_locations = [os.path.join(
            settings_path, self.app_subfolder, self.sub_command_name,
            *self.arg_name.split("-")) for settings_path in self.settings_dirs]
        main_locations = [os.path.join(
            settings_path, self.app_subfolder, *self.arg_name.split("-"))
            for settings_path in self.settings_dirs]
        search_locations.extend(main_locations)
        search_locations.append(os.getcwd())
        return search_locations


class Value(ComplexType):
    """
    The simple nested value option.
    """

    def resolve(self, value):
        """
        Returns the argument value
        """
        return value


class AdditionalOptionsType(ComplexType):
    """
    This is a custom type to handle passing additional arguments to some part
    of infrared.

    Format should be --additional-args=option1=value1;option2=value2
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


class YamlFile(ComplexType):
    """
    The complex type for yaml arguments.
    """

    FILE_EXTENSION = ['yml', 'yaml']

    def resolve(self, value):
        """
        Transforms yaml file to the dict
        :return:
        """
        search_paths = self.get_file_locations()
        return utils.load_yaml(value,
                               *search_paths)

    def get_allowed_values(self):
        res = []

        # except the main folder where we can have a lot of yaml files.
        locations = self.get_file_locations()[:-1]

        for folder in locations:
            for ext in self.FILE_EXTENSION:
                res.extend(glob.glob(folder + "/*." + ext))

        return map(os.path.basename, res)


class ListOfYamls(YamlFile):
    """
    Builds dicts from smaller YAML files.

    Type value should be the comma separated string of files to load with or
     without yml extension. This list can have only one element.

     Values examples:
        item1,item2,item3
        item1.yml

    Will search for files in the spec settings directories before trying
        to resolve absolute path.

    For the argument name is "arg-name" arg value is "item1,item2"
     and of subparser "SUBCOMMAND" of application "APP", the default
     search paths would be:

         settings_dir/APP/SUBCOMMAND/arg/name/{item1.yml, item2.yml}
         settings_dir/APP/arg/name/{item1.yml, item2.yml}
         {item1.yml, item2.yml}

    The type value will be the dict in the format:
      item1:
         <content of item1.yml>
      item2:
         <content of item2.yml>
      ...
    """

    def get_allowed_values(self):
        values = super(ListOfYamls, self).get_allowed_values()
        return [os.path.splitext(os.path.basename(file_name))[0]
                for file_name in values]

    def resolve(self, value):
        search_paths = self.get_file_locations()

        result = {}
        if value is not None:
            # validate value. Check that we have comma separated values
            pattern = re.compile("^[-\w\s\.]+(?:,[-\w\s]*)*$")
            if pattern.match(value) is None:
                raise exceptions.IRWrongYamlListFormat(value)

            for item in value.split(','):
                item_name, item_file = self._construct_name(item)
                item_dict = utils.load_yaml(item_file, *search_paths)
                result[item_name] = item_dict

        return result

    def _construct_name(self, item):
        """
        Gets the name of the file to load.
        """
        with_extension = False
        for extension in self.FILE_EXTENSION:
            ext = "." + extension
            if item.endswith(ext):
                result_file = item
                result_name = item[:-len(ext)]
                with_extension = True
                break
        if not with_extension:
            result_file = item + "." + self.FILE_EXTENSION[0]
            result_name = item

        return result_name, result_file


class Topology(ComplexType):
    """
    Represents the topology complex type.
    """

    def resolve(self, value):
        """
        Reads the topology data.
        """
        topology_dirs = [os.path.join(path, self.app_subfolder, 'topology')
                         for path in self.settings_dirs]

        topology_dict = {}
        for topology_item in value.split(','):
            pattern = re.compile("^[A-Za-z]+:[0-9]+$")
            if pattern.match(topology_item) is None:
                pattern = re.compile("^[0-9]+_[A-Za-z]+$")
                if pattern.match(topology_item) is None:
                    raise exceptions.IRWrongTopologyFormat(value)
                number, node_type = topology_item.split('_')
                LOG.warning("The '{}' topology format is deprecated and will "
                            "be removed in future versions. "
                            "Please see `--help` "
                            "for proper format".format(topology_item))
            else:
                node_type, number = topology_item.split(':')

            # Remove white spaces
            node_type = node_type.strip()

            topology_dict[node_type] = \
                utils.load_yaml(node_type + ".yml", *topology_dirs)
            topology_dict[node_type]['amount'] = int(number)

        return topology_dict


# register custom actions
ACTIONS = {
    'read-config': ReadConfigAction,
    'generate-config': GenerateConfigAction
}

# register complex Types. See ComplexType to implement new types
COMPLEX_TYPES = {
    'Value': Value,
    'YamlFile': YamlFile,
    'ListOfYamls': ListOfYamls,
    'Topology': Topology,
    'AdditionalArgs': AdditionalOptionsType
}
