"""
This module is used to read command line arguments and validate them
according to the specification (spec) files.
"""

import argparse
import collections
import ConfigParser
import glob
import os
import re
import sys
import yaml
from copy import deepcopy

from cli import utils, logger, exceptions

LOG = logger.LOG

BUILTINS = sys.modules[
    'builtins' if sys.version_info.major == 3 else '__builtin__']
TYPES = {builtin: getattr(BUILTINS, builtin) for builtin in vars(BUILTINS)}
TYPES['suppress'] = argparse.SUPPRESS

OPTION_ARGPARSE_ATTRIBUTES = ['action', 'nargs', 'const', 'default', 'choices',
                              'required', 'help', 'metavar', 'type', 'version']


class Spec(object):
    """
    The spec manager.
    """

    @classmethod
    def from_folder(cls, settings_folder, app_name, file_ext='spec'):
        """
        Reads spec file from the settings folder and generate Spec object.
        :param settings_folder: the root settings file
        :param app_name: the application name (provisioner/installer/tester)
        :param file_ext: the spec file extension.
        :return: the Spec instance.
        """
        # look for common specs in the root of the settings file
        spec_files = []
        spec_files.extend(glob.glob('./' + settings_folder + '/*' + file_ext))

        # look for all the spec files for an app
        root_folder = os.path.join(settings_folder, app_name)

        for root, _, files in os.walk(root_folder):
            spec_files.extend([os.path.join(root, a_file) for a_file in files
                               if a_file.endswith(file_ext)])

        return cls.from_files(settings_folder, app_name, *spec_files)

    @classmethod
    def from_files(cls, settings_folder, app_name, *spec_files):
        """
        Reads specs files and constructs the parser isinstance
        """
        result = {}
        for spec_file in spec_files:
            with open(spec_file) as stream:
                spec = yaml.load(stream)
                utils.dict_merge(
                    result, spec, utils.ConflictResolver.append_list_resolver)

        return Spec(result, settings_folder, app_name)

    def __init__(self, spec_dict, settings_folder, app_name):
        self.app_name = app_name
        self.settings_folder = settings_folder
        self.spec_dict = spec_dict
        self.validate_spec()
        # make structure of the dict flat
        # 1. handle include_groups directive in root parser
        parser_dict = self.spec_dict['command']
        self._include_groups(parser_dict)
        # 2. Include groups for all subparsers
        for subparser in parser_dict.get('subcommands', []):
            self._include_groups(subparser)

    def _include_groups(self, parser_dict):
        for group in parser_dict.get('include_groups', []):
            # ensure we have that group
            grp_dict = next(
                (grp for grp in self.spec_dict['groups']
                 if grp['name'] == group),
                None)
            if grp_dict is None:
                raise SpecParserException(
                    "Unable to include group '{}' in '{}' parser. "
                    "Group was not found!".format(
                        group,
                        parser_dict['name']))

            parser_groups_list = parser_dict.get('groups', [])
            parser_groups_list.append(grp_dict)
            parser_dict['groups'] = parser_groups_list

    def _get_all_options(self, parser_dict):
        result = []
        for group in parser_dict.get('groups', []):
            for option in group.get('options', []):
                result.append(option)
        return result

    def _get_parser_options(self, parser_name):
        options = []
        if parser_name == 'root':
            options = self._get_all_options(self.spec_dict['command'])
        else:
            for subparser in self.spec_dict['command'].get('subcommands', []):
                if subparser['name'] == parser_name:
                    options = self._get_all_options(subparser)
                    break
        return options

    def _get_defaults(self, default_getter_func):
        """
        Gets the defaults value according to the spec file.
        """

        def process_parser(parser_dict, is_subparser):
            """
            Retrieves default values from a parser.
            """
            result = collections.defaultdict(dict)
            all_options = self._get_all_options(parser_dict)
            for option in all_options:
                default_value = default_getter_func(option)
                if default_value is not None:
                    if is_subparser:
                        sub = parser_dict['name']
                        result[sub][option['name']] = default_value
                    else:
                        result['root'][option['name']] = default_value

            return result

        res = process_parser(self.spec_dict['command'], False)
        for subparser in self.spec_dict['command'].get('subcommands', []):
            utils.dict_merge(
                res,
                process_parser(subparser, True))
        return res

    def get_env_defaults(self):
        """
        Gets the argument's  defaults values from the environment.
        """

        def env_getter(option):
            """
            The getter fucntion to retrieve the env varible for arument.
            """
            env_name = option['name'].replace('-', '_').upper()
            return os.environ.get(env_name, None)

        return self._get_defaults(env_getter)

    def get_spec_defaults(self):
        """
        Gets the arguments defaults value from the spec and other sources.
        """

        def spec_default_getter(option):
            """
            The getter function to retrieve the default value from spec
            """
            default_value = None
            if option.get('default', None) is not None:
                default_value = option['default']
            elif option.get('action', None) in ['store_true']:
                default_value = False
            return default_value

        return self._get_defaults(spec_default_getter)

    def get_config_args(self, cli_args):
        """
        Gets the args's from the configuration file
        """
        condig_options = {}
        condig_options['root'] = filter(
            lambda option: option.get('action', None) == 'read-config',
            self._get_all_options(self.spec_dict['command']))
        for subparser in self.spec_dict['command'].get('subcommands', []):
            condig_options[subparser['name']] = filter(
                lambda option: option.get('action', None) == 'read-config',
                self._get_all_options(subparser))

        # now check what parser we have from cli
        file_result = collections.defaultdict(dict)
        for parser_name, parser_args_dict in cli_args.items():
            for file_option in condig_options.get(parser_name, []):
                if file_option['name'] in parser_args_dict:
                    # we have config option. saving it.
                    utils.dict_merge(
                        file_result[parser_name],
                        parser_args_dict[file_option['name']])
                    # remove from cli args
                    parser_args_dict.pop(file_option['name'])

        return file_result

    def generate_config_file(self, cli_args, spec_defaults):

        def put_option(out_config, parser_name, opt_name, value):
            for opt_help in option.get('help', '').split('\n'):
                help_opt = '# ' + opt_help

                # add help comment
                if out_config.has_option(parser_name, help_opt):
                    out_config.remove_option(help_opt)
                out_config.set(
                    parser_name, help_opt)

            if out_config.has_option(parser_name, opt_name):
                value = out_config.get(parser_name, opt_name)
                out_config.remove_option(parser_name, opt_name)

            out_config.set(
                parser_name,
                opt_name,
                value)

        file_generated = False
        condig_options = {}
        condig_options['root'] = filter(
            lambda option: option.get('action', None) == 'generate-config',
            self._get_all_options(self.spec_dict['command']))
        for subparser in self.spec_dict['command'].get('subcommands', []):
            condig_options[subparser['name']] = filter(
                lambda option: option.get('action', None) == 'generate-config',
                self._get_all_options(subparser))

        # load generate config file for all the parsers
        for parser_name, parser_args_dict in cli_args.items():
            for generate_option in condig_options.get(parser_name, []):
                if generate_option['name'] in parser_args_dict:
                    # we have to generate config.
                    # put command default arguments to the file
                    options_to_save = self._get_parser_options(parser_name)
                    out_config = ConfigParser.ConfigParser(allow_no_value=True)
                    file_name = parser_args_dict[generate_option['name']]

                    if os.path.exists(file_name):
                        # todo(obaranov) comments from other section will be
                        # removed.
                        out_config.read(file_name)

                    if not out_config.has_section(parser_name):
                        out_config.add_section(parser_name)

                    for option in options_to_save:
                        opt_name = option['name']
                        if opt_name in spec_defaults[parser_name]:
                            put_option(
                                out_config,
                                parser_name,
                                opt_name,
                                spec_defaults[parser_name][opt_name])
                        elif option.get('required', False):
                            put_option(
                                out_config,
                                parser_name,
                                opt_name,
                                "Required argument. "
                                "Edit with one of the allowed values OR "
                                "override with "
                                "CLI: --{}=<option>".format(opt_name))

                    with open(file_name, 'w') as configfile:  # save
                        out_config.write(configfile)
                    file_generated = True
        return file_generated

    def resolve_complex_types(self, args):
        # todo (obaranov) remove hardcoded settings.
        for parser_name, parser_dict in args.items():
            spec_complex_options = [opt for opt in
                                    self._get_parser_options(parser_name) if
                                    opt.get('complex_type', None)]
            for spec_option in spec_complex_options:
                option_name = spec_option['name']
                if option_name in parser_dict:
                    # we have complex action to resolve
                    type_name = spec_option['complex_type']
                    option_value = parser_dict[option_name]
                    action = self.create_complex_action(
                        parser_name,
                        type_name,
                        option_name)

                    # resolving value
                    parser_dict[option_name] = action.resolve(option_value)

    def create_complex_action(self, subcommand, type_name, option_name):
        complex_action = COMPLEX_TYPES.get(
            type_name, None)
        if complex_action is None:
            raise SpecParserException(
                "Unknown complex type: {}".format(
                    type_name))
        return complex_action(
            option_name,
            self.settings_folder,
            self.app_name,
            subcommand)

    def parse_args(self):
        spec_defaults = self.get_spec_defaults()
        env_defaults = self.get_env_defaults()
        cli_args = CliParser.parse_args(self)

        file_args = self.get_config_args(cli_args)

        # generate config file if arg is present and exit
        if self.generate_config_file(cli_args, spec_defaults):
            LOG.warning("Config file generated. Exiting.")
            return None

        # print warnings when something was overridden from non-cli source.
        self.validate_arg_sources(cli_args,
                                  env_defaults,
                                  file_args,
                                  spec_defaults)

        # merge defaults into one
        utils.dict_merge(spec_defaults, env_defaults)
        # now filter defaults to have only parser defined in cli
        defaults = {key: spec_defaults[key] for key in cli_args.keys()}

        utils.dict_merge(defaults, file_args)
        utils.dict_merge(defaults, cli_args)
        self.validate_requires_args(defaults)

        # now resolve complex types.
        self.resolve_complex_types(defaults)
        return defaults

    def validate_arg_sources(self, cli_args, env_defaults, file_args,
                             spec_defaults):

        def warn_diff(diff, command_name, cmd_dict, source_name):
            if diff:
                for arg_name in diff:
                    value = cmd_dict[arg_name]
                    LOG.warning(
                        "[{}] Argument '{}' was set to"
                        " '{}' from the {} source.".format(
                            command_name, arg_name, value, source_name))

        for command, command_dict in cli_args.items():
            file_dict = file_args.get(command, {})
            self.validate_unrecognized_arguments(command, file_dict)
            file_diff = set(file_dict.keys()) - set(command_dict.keys())
            warn_diff(file_diff, command, file_dict, 'config file')

            env_dict = env_defaults.get(command, {})
            env_diff = set(env_dict.keys()) - set(
                command_dict.keys()) - file_diff
            warn_diff(env_diff, command, env_dict, 'environment variables')

            def_dict = spec_defaults.get(command, {})
            default_diff = set(def_dict.keys()) - set(
                command_dict.keys()) - file_diff - env_diff
            warn_diff(default_diff, command, def_dict, 'spec defaults')

    def validate_spec(self):
        """
        Validates the specification.
        """
        assert 'command' in self.spec_dict

    def validate_unrecognized_arguments(self, command_name, command_dict):
        # get expected options
        if command_name == 'root':
            options = self._get_all_options(self.spec_dict['command'])
        else:
            subparser = next((subparser for subparser in
                              self.spec_dict['command'].get('subcommands', [])
                              if subparser['name'] == command_name), None)
            options = self._get_all_options(subparser)

        options = map(lambda opt: opt['name'], options)
        for arg_name, arg_value in command_dict.items():
            if arg_name not in options:
                LOG.warning(
                    "[{}] Unrecognized argument in config file: '{}'. "
                    "Ignoring.".format(command_name, arg_name))
                command_dict.pop(arg_name)

    def validate_requires_args(self, args):
        """
        Validates the resulting args.
        :return:
        """

        def validate_parser(parser_name, expected_options, parser_args):
            result = True
            for option in expected_options:
                name = option['name']

                # check required options.
                if option.get('required', False) and name not in parser_args:
                    LOG.error(
                        "Required argument '{}' is not set "
                        "for '{}' command".format(name, parser_name))
                    result = False

            if not result:
                LOG.warning(
                    "Received arguments for "
                    "'{}' command: {}".format(parser_name, parser_args))

            return result

        # go through the options from spec.
        root_options = self._get_all_options(self.spec_dict['command'])
        validate_parser('root', root_options, args['root'])
        res = True
        for subparser in self.spec_dict['command'].get('subcommands', []):
            sub_name = subparser['name']
            if sub_name in args:
                res = validate_parser(sub_name,
                                      self._get_all_options(subparser),
                                      args[sub_name])
        if not res:
            os._exit(1)


class CliParser(object):
    """
    Allows to handle the CLI arguments.
    """

    @classmethod
    def parse_args(cls, spec):
        parser_dict = spec.spec_dict['command']
        arg_parser = argparse.ArgumentParser(
            description=parser_dict.get(
                'description', ''),
            formatter_class=parser_dict.get(
                'formatter_class', argparse.RawTextHelpFormatter))

        cls._add_groups(spec, arg_parser, parser_dict)

        # process subparsers
        subparsers = parser_dict.get('subcommands', [])
        if subparsers:
            dest_path = 'command0'
            arg_subparser = arg_parser.add_subparsers(dest=dest_path)

            for subparser_dict in parser_dict.get('subcommands', []):
                cmd_parser = arg_subparser.add_parser(
                    subparser_dict['name'],
                    help=subparser_dict.get('help', ''),
                    description=subparser_dict.get('description', ''),
                    formatter_class=parser_dict.get(
                        'formatter_class', argparse.RawTextHelpFormatter))

                cls._add_groups(
                    spec,
                    cmd_parser,
                    subparser_dict,
                    path_prefix=dest_path)
        # finally get the args
        parse_args = arg_parser.parse_args().__dict__

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
                result['root'][arg] = value

        return result

    @classmethod
    def _add_groups(cls, spec, arg_parser, parser_data, path_prefix=''):
        """
        Adds groups to the parser.
        """
        options = []
        # add 'private' parser groups
        for grp_dict in parser_data.get('groups', []):
            group = arg_parser.add_argument_group(grp_dict['name'])
            # add options to the group
            for opt_dict in grp_dict.get('options', []):
                options.append(
                    cls._add_argument(spec, parser_data.get('name', 'root'),
                                      group, opt_dict, path_prefix))
        return options

    @classmethod
    def _add_argument(cls, spec, subparser, group, option_data,
                      path_prefix=''):
        """
        Adds argument to the group.
        """
        opt_args = []
        opt_kwargs = {}
        if 'short' in option_data:
            opt_args.append('-{}'.format(option_data['short']))
        opt_args.append('--{}'.format(option_data['name']))

        # add prefix to ensure we can group subcommand arguments later
        opt_kwargs['dest'] = option_data.get(
            'dest', path_prefix + option_data['name'])
        if 'type' in option_data:
            opt_kwargs['type'] = TYPES.get(option_data['type'])

        for option_key in OPTION_ARGPARSE_ATTRIBUTES:
            if option_key != 'type' and option_key in option_data:
                opt_kwargs[option_key] = option_data[option_key]
        # set correct metavar to have correct name in the usage statement
        if 'metavar' not in opt_kwargs and \
                opt_kwargs.get('action', None) not in \
                ['count', 'help', 'store_true']:
            opt_kwargs['metavar'] = option_data['name'].upper()

        # resolve custom action
        if 'action' in opt_kwargs and opt_kwargs['action'] in ACTIONS:
            opt_kwargs['action'] = ACTIONS[opt_kwargs['action']]

        # print default values to the help
        if opt_kwargs.get('default', None):
            opt_kwargs['help'] += "\nDefault value: {}".format(
                opt_kwargs['default'])

        # put allowed values to the help.
        allowed_values = []
        if opt_kwargs.get('choices', None):
            allowed_values = opt_kwargs['choices']
        elif option_data.get('complex_type', None):
            action = spec.create_complex_action(
                subparser,
                option_data['complex_type'],
                option_data['name'])

            # resolving value
            allowed_values = action.get_allowed_values()

        if allowed_values:
            opt_kwargs['help'] += "\nAllowed values: {}".format(
                allowed_values)

        # update help
        option_data['help'] = opt_kwargs['help']

        # pop default
        result = deepcopy(opt_kwargs)
        if not any(arg in sys.argv for arg in ['-h', '--help']):
            opt_kwargs.pop('default', None)
            opt_kwargs['default'] = argparse.SUPPRESS
            opt_kwargs.pop('required', None)

        group.add_argument(*opt_args, **opt_kwargs)
        return result


class SpecParserException(Exception):
    """
    The spec parser specific exception.
    """
    pass


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

    def __init__(self, arg_name,
                 settings_dir,
                 app_name,
                 sub_command_name):
        self.arg_name = arg_name
        self.sub_command_name = sub_command_name
        self.app_name = app_name
        self.settings_dir = settings_dir

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


class YamlFile(ComplexType):
    """
    The complex type for yaml arguments.
    """

    FILE_EXTENSION = ['yml', 'yaml']

    def get_file_locations(self):
        """
        Get the possible locations (folders) where the
        yaml files can be stored.
        """

        base_dir = os.path.join(self.settings_dir, self.app_name)
        search_first = os.path.join(base_dir,
                                    self.sub_command_name,
                                    *self.arg_name.split("-"))
        search_second = os.path.join(base_dir,
                                     *self.arg_name.split("-"))
        return search_first, search_second, "."

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

        # except the root folder where we can have a lot of yaml files.
        locations = self.get_file_locations()[:-1]

        for folder in locations:
            for ext in self.FILE_EXTENSION:
                res.extend(glob.glob(folder + "/*." + ext))

        return map(os.path.basename, res)


class Topology(ComplexType):
    """
    Represents the topology complex type.
    """

    def resolve(self, value):
        """
        Reads the topology data.
        """
        topology_dir = os.path.join(
            self.settings_dir, self.app_name, 'topology')
        topology_dict = {}
        for topology_item in value.split(','):

            node_type, number = None, None

            pattern = re.compile("^[A-Za-z]+:[0-9]+$")
            if pattern.match(topology_item) is None:
                pattern = re.compile("^[0-9]+_[A-Za-z]+$")
                if pattern.match(topology_item) is None:
                    raise exceptions.IRWrongTopologyFormat(value)
                number, node_type = topology_item.split('_')
                LOG.warning("This topology format is deprecated and will be "
                            "removed in future versions. Please see `--help` "
                            "for proper format")
            else:
                node_type, number = topology_item.split(':')

            # Remove white spaces
            node_type = node_type.strip()

            # todo(obaraov): consider moving topology to config on constant.
            topology_dict[node_type] = \
                utils.load_yaml(node_type + ".yml", topology_dir)
            topology_dict[node_type]['amount'] = int(number)

        return topology_dict


# register custom actions
ACTIONS = {
    'read-config': ReadConfigAction,
    'generate-config': GenerateConfigAction
}

COMPLEX_TYPES = {
    'YamlFile': YamlFile,
    'Topology': Topology
}
