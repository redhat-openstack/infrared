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


class OptionState(object):
    """
    Describes different stat of the options.
    """
    UNRECOGNIZED = 'unrecognized'
    IS_SET = 'is set'
    NOT_SET = 'is no set'


class Spec(object):
    """
    Parses the input arguments from different sources (cli, file, env)
    """

    @classmethod
    def from_folder(cls, settings_folders, app_name, file_ext='spec'):
        """
        Reads spec file from the settings folder and generate Spec object.
        :param settings_folders: the main settings folder
        :param app_name: the application name (provisioner/installer/tester)
        :param file_ext: the spec file extension.
        :return: the Spec instance.
        """
        # look for common specs in the main of the settings file
        spec_files = []
        for settings_folder in settings_folders:
            spec_files.extend(
                glob.glob('./' + settings_folder + '/*' + file_ext))

            # look for all the spec files for an app
            main_folder = os.path.join(settings_folder, app_name)

            for main, _, files in os.walk(main_folder):
                spec_files.extend(
                    [os.path.join(main, a_file) for a_file in files
                     if a_file.endswith(file_ext)])

        return cls.from_files(settings_folders, app_name, *spec_files)

    @classmethod
    def from_files(cls, settings_folders, app_name, *spec_files):
        """
        Reads specs files and constructs the parser isinstance
        """
        result = {}
        for spec_file in spec_files:
            with open(spec_file) as stream:
                spec = yaml.load(stream)
                utils.dict_merge(
                    result,
                    spec,
                    utils.ConflictResolver.unique_append_list_resolver)

        return Spec(result, settings_folders, app_name)

    def __init__(self, spec_dict, settings_folders, app_name):
        self.app_name = app_name
        self.settings_folders = settings_folders
        self.spec_helper = SpecDictHelper(spec_dict)

    def _get_defaults(self, default_getter_func):
        """
        Gets the defaults value according to the spec file.
        """

        def process_parser(parser_dict, is_main):
            """
            Retrieves default values from a parser.
            """
            result = collections.defaultdict(dict)
            all_options = self.spec_helper.get_all_options_spec(parser_dict)
            for option in all_options:
                default_value = default_getter_func(option)
                if default_value is not None:
                    if not is_main:
                        sub = parser_dict['name']
                        result[sub][option['name']] = default_value
                    else:
                        result['main'][option['name']] = default_value

            return result

        res = {}
        for command, is_main_cmd in self.spec_helper.iterate_commands():
            utils.dict_merge(
                res,
                process_parser(command, is_main_cmd))

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

    def get_config_file_args(self, cli_args):
        """
        Gets the args's from the configuration file
        """

        file_result = collections.defaultdict(dict)
        for command_name, command_dict in cli_args.items():
            for arg_name, arg_value in command_dict.items():
                option_spec = self.spec_helper.get_option_spec(
                    command_name, arg_name)
                if option_spec and option_spec.get(
                        'action', '') == 'read-config':
                    # we have config option. saving it.
                    utils.dict_merge(
                        file_result[command_name],
                        command_dict[arg_name])
                    # remove from cli args
                    command_dict.pop(arg_name)

        return file_result

    def generate_config_file(self, cli_args, spec_defaults):
        """
        Generates the configuration file
        :param cli_args:  the list of cli arguments
        :param spec_defaults: the default values.
        """

        def put_option(config, parser_name, option_name, value):
            for opt_help in option.get('help', '').split('\n'):
                help_opt = '# ' + opt_help

                # add help comment
                if config.has_option(parser_name, help_opt):
                    config.remove_option(parser_name, help_opt)
                config.set(
                    parser_name, help_opt)

            if config.has_option(parser_name, option_name):
                value = config.get(parser_name, option_name)
                config.remove_option(parser_name, option_name)

            config.set(
                parser_name,
                option_name,
                value)

        file_generated = False

        # load generate config file for all the parsers
        for command_name, command_dict in cli_args.items():
            for arg_name, arg_value in command_dict.items():
                option_spec = self.spec_helper.get_option_spec(
                    command_name, arg_name)
                if option_spec and option_spec.get(
                        'action', '') == 'generate-config':
                    options_to_save = \
                        self.spec_helper.get_command_options_spec(command_name)
                    out_config = ConfigParser.ConfigParser(allow_no_value=True)

                    if os.path.exists(arg_value):
                        # todo(obaranov) comments from other section will be
                        # removed.
                        out_config.read(arg_value)

                    if not out_config.has_section(command_name):
                        out_config.add_section(command_name)

                    for option in options_to_save:
                        opt_name = option['name']
                        if opt_name in spec_defaults[command_name]:
                            put_option(
                                out_config,
                                command_name,
                                opt_name,
                                spec_defaults[command_name][opt_name])
                        elif option.get('required', False):
                            put_option(
                                out_config,
                                command_name,
                                opt_name,
                                "Required argument. "
                                "Edit with one of the allowed values OR "
                                "override with "
                                "CLI: --{}=<option>".format(opt_name))
                    with open(arg_value, 'w') as configfile:  # save
                        out_config.write(configfile)
                    file_generated = True

        return file_generated

    def resolve_complex_types(self, args):
        """
        Transforms the arguments with complex_type defined.
        :param args: the list of received arguments.
        """
        for parser_name, parser_dict in args.items():
            spec_complex_options = [opt for opt in
                                    self.spec_helper.get_command_options_spec(
                                        parser_name) if
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
        """
        The builder method for the complex type
        :param subcommand: the command name
        :param type_name: the complex type name
        :param option_name: the option name
        :return: the complex type instance
        """
        complex_action = COMPLEX_TYPES.get(
            type_name, None)
        if complex_action is None:
            raise SpecParserException(
                "Unknown complex type: {}".format(type_name))
        return complex_action(
            option_name,
            self.settings_folders,
            self.app_name,
            subcommand)

    def parse_args(self):
        """
        Parses all the arguments (cli, file, env) and returns two dicts:
            * command arguments dict (arguments to control the IR logic)
            * nested arguments dict (arguments to pass to the playbooks)
        """

        spec_defaults = self.get_spec_defaults()
        env_defaults = self.get_env_defaults()
        cli_args = CliParser.parse_args(self)
        file_args = self.get_config_file_args(cli_args)

        # generate config file and exit
        if self.generate_config_file(cli_args, spec_defaults):
            LOG.warning("Config file has been generated. Exiting.")
            return None

        # print warnings when something was overridden from non-cli source.
        self.validate_arg_sources(cli_args,
                                  env_defaults,
                                  file_args,
                                  spec_defaults)

        # merge defaults into one
        utils.dict_merge(spec_defaults, env_defaults)
        # now filter defaults to have only parser defined in cli
        defaults = {key: spec_defaults[key] for key in cli_args.keys() if
                    key in spec_defaults}

        utils.dict_merge(defaults, file_args)
        utils.dict_merge(defaults, cli_args)
        self.validate_requires_args(defaults)

        # now resolve complex types.
        self.resolve_complex_types(defaults)

        # now maybe split all the args for nested and non-nested
        return self.get_nested_and_control_args(defaults)

    def validate_arg_sources(self, cli_args, env_defaults, file_args,
                             spec_defaults):
        """
        Validates and prints the arguments source.
        :param cli_args: the dict of arguments from cli
        :param env_defaults:  the dict of arguments from env
        :param file_args:  the dict of arguments from files
        :param spec_defaults:  the default values from spec files
        """

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

    def validate_unrecognized_arguments(self, command_name, command_dict):
        """
        Verify the file arguments do not have unrecognized arguments.
        :param command_name: the command name (main, virsh, etc)
        :param command_dict: the command arguments.
        """
        for arg_name, arg_value in command_dict.items():
            if self.spec_helper.get_option_state(command_name, arg_name, {}) \
                    == OptionState.UNRECOGNIZED:
                LOG.warning(
                    "[{}] Unrecognized argument in config file: '{}'. "
                    "Ignoring.".format(command_name, arg_name))
                command_dict.pop(arg_name)

    def _get_conditionally_required_args(
            self, command_name, options_spec, args):
        """
        Gets the arguments names with the required_when keyword
        :param command_name: the command name.
        :param options_spec:  the list of command spec options.
        :param args: the received input arguments
        """
        res = []
        for option_spec in options_spec:
            if option_spec and 'required_when' in option_spec:
                # validate condition
                req_arg, req_value = option_spec['required_when'].split('==')
                if args.get(command_name, {}).get(
                        req_arg.strip(), None) == req_value.strip() \
                        and self.spec_helper.get_option_state(
                            command_name,
                            option_spec['name'], args) == OptionState.NOT_SET:
                    res.append(option_spec['name'])
        return res

    def validate_requires_args(self, args):
        """
        Check if all the required arguments have been provided.
        """

        silent_args = self.spec_helper.get_silent_args(args)

        def validate_parser(parser_name, expected_options, parser_args):
            result = True
            condition_req_args = self._get_conditionally_required_args(
                parser_name, expected_options, args)

            for option in expected_options:
                name = option['name']

                # check required options.
                if (option.get('required', False) and
                            name not in parser_args or
                            option['name'] in condition_req_args) and \
                                name not in silent_args:
                    LOG.error(
                        "Required argument '{}' is not set "
                        "for '{}' command".format(name, parser_name))
                    result = False

            if not result:
                LOG.warning(
                    "Received arguments for "
                    "'{}' command: {}".format(parser_name, parser_args))

            return result

        res = []
        for command_data, is_main in self.spec_helper.iterate_commands():
            cmd_name = command_data['name'] if not is_main else 'main'
            if cmd_name in args:
                res.append(
                    validate_parser(
                        cmd_name,
                        self.spec_helper.get_command_options_spec(cmd_name),
                        args[cmd_name]))
        if not all(res):
            os._exit(1)

    def get_nested_and_control_args(self, args):
        """
        Constructs control and nested args.

        Controls arguments control the IR behavior. These arguments
            will not be put into the spec yml file

        Nested arguments are used by the Ansible playbooks and will be put
            into the spec yml. file.
        :param args: the collected list of args.
        :return: The pair of flat dicts (control_args, nested_args)
        """
        # returns flat dicts
        nested = {}
        control_args = {}
        for command_name, command_dict in args.items():
            for arg_name, arg_value in command_dict.items():
                arg_spec = self.spec_helper.get_option_spec(
                    command_name, arg_name)
                if arg_spec and arg_spec.get('nested', True):
                    if arg_name in nested:
                        LOG.warning(
                            "Duplicating nested argument '{}'. "
                            "Old value: '{}'. New value: '{}']".format(
                                arg_name, nested[arg_name], arg_value))
                    nested[arg_name] = arg_value
                else:
                    if arg_name in control_args:
                        LOG.warning(
                            "Duplicating nested argument '{}'."
                            "Old value: '{}'. New value: '{}']".format(
                                arg_name, control_args[arg_name], arg_value))
                    control_args[arg_name] = arg_value

        return nested, control_args


class SpecDictHelper(object):
    """
    Controls the spec dicts and provides useful methods to get spec info.
    """

    def __init__(self, spec_dict):
        self.spec_dict = spec_dict
        self.validate_spec()
        # make structure of the dict flat
        # 1. handle include_groups directive in main parser
        parser_dict = self.spec_dict['command']
        self.include_groups(parser_dict)
        # 2. Include groups for all subparsers
        for subparser in parser_dict.get('subcommands', []):
            self.include_groups(subparser)

    def iterate_commands(self):
        """
        Iterates over the main commands and subcommands
        :return: the iterator. Each element is a tuple:
            (command_data|dict, is_main_command|bool)
        """
        yield self.spec_dict['command'], True
        for subparser in self.spec_dict['command'].get('subcommands', []):
            yield subparser, False

    def get_all_options_spec(self, parser_dict):
        result = []
        for group in parser_dict.get('groups', []):
            for option in group.get('options', []):
                result.append(option)
        return result

    def get_command_options_spec(self, command_name):
        """
        Gets all the options for the specified command (main, virsh, ospd, etc)
        :param command_name: the command name
        :return: the list of all command options
        """
        options = []
        if command_name == 'main':
            options = self.get_all_options_spec(self.spec_dict['command'])
        else:
            for subparser in self.spec_dict['command'].get('subcommands', []):
                if subparser['name'] == command_name:
                    options = self.get_all_options_spec(subparser)
                    break
        return options

    def get_option_spec(self, command_name, argument_name):
        """
        Gets the specification for the specified option name
        """
        options = self.get_command_options_spec(command_name)
        return next((opt for opt in options
                     if opt['name'] == argument_name), None)

    def get_option_state(self, command_name, option_name, args):
        """
        Gets the option state.
        :param command_name: The command name
        :param option_name: The option name to analyze
        :param args: The received arguments.
        """
        option_spec = self.get_option_spec(command_name, option_name)

        if not option_spec:
            res = OptionState.UNRECOGNIZED

        elif option_name not in args.get(command_name, {}):
            res = OptionState.NOT_SET
        else:
            option_value = args[command_name][option_name]
            if option_spec.get('action', '') in ['store_true'] \
                    and option_value is False:
                res = OptionState.NOT_SET
            else:
                res = OptionState.IS_SET

        return res

    def get_silent_args(self, args):
        """
        Gets the list of options names that should silent'ed
        :param args: The received arguments.
        """
        silent_args_names = []
        for command_name, command_dict in args.items():
            for arg_name, arg_value in command_dict.items():
                arg_spec = self.get_option_spec(command_name, arg_name)
                if arg_spec and 'silent' in arg_spec:
                    if self.get_option_state(
                            command_name,
                            arg_name,
                            args) == OptionState.IS_SET:
                        silent_args_names.extend(arg_spec['silent'])

        return list(set(silent_args_names))

    def validate_spec(self):
        """
        Validates the specification.
        """
        assert 'command' in self.spec_dict

    def include_groups(self, parser_dict):
        """
        Resolves the include dicst directive in the spec files.
        """
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
            parser_groups_list.append(deepcopy(grp_dict))
            parser_dict['groups'] = parser_groups_list


class CliParser(object):
    """
    Allows to handle the CLI arguments.
    """

    @classmethod
    def parse_args(cls, spec):
        parser_dict = spec.spec_helper.spec_dict['command']
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
                result['main'][arg] = value

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
                    cls._add_argument(spec, parser_data.get('name', 'main'),
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
        if 'metavar' not in opt_kwargs and opt_kwargs.get(
                'action', None) not in ['count', 'help', 'store_true']:
            opt_kwargs['metavar'] = option_data['name'].upper()

        # resolve custom action
        if 'action' in opt_kwargs and opt_kwargs['action'] in ACTIONS:
            opt_kwargs['action'] = ACTIONS[opt_kwargs['action']]

        # print default values to the help
        if opt_kwargs.get('default', None):
            opt_kwargs['help'] += "\nDefault value: {}".format(
                opt_kwargs['default'])

        # print silent args to the help
        if option_data.get('silent', None):
            opt_kwargs['help'] += "\nWhen this option is set the following " \
                                  "options are not required: {}".format(
                option_data['silent'])
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
                 settings_dirs,
                 app_name,
                 sub_command_name):
        self.arg_name = arg_name
        self.sub_command_name = sub_command_name
        self.app_name = app_name
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
            settings_path, self.app_name, self.sub_command_name,
            *self.arg_name.split("-"))
                            for settings_path in self.settings_dirs]
        main_locations = [os.path.join(
            settings_path, self.app_name, *self.arg_name.split("-"))
                          for settings_path in self.settings_dirs]
        search_locations.extend(main_locations)
        search_locations.append(os.getcwd())
        return search_locations


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


class Topology(ComplexType):
    """
    Represents the topology complex type.
    """

    def resolve(self, value):
        """
        Reads the topology data.
        """
        topology_dirs = [os.path.join(path, self.app_name, 'topology')
                         for path in self.settings_dirs]

        topology_dict = {}
        for topology_item in value.split(','):
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

            topology_dict[node_type] = \
                utils.load_yaml(node_type + ".yml", *topology_dirs)
            topology_dict[node_type]['amount'] = int(number)

        return topology_dict


# register custom actions
ACTIONS = {
    'read-config': ReadConfigAction,
    'generate-config': GenerateConfigAction
}

# register complex Types. See ComplexType by type to implement new types
COMPLEX_TYPES = {
    'YamlFile': YamlFile,
    'Topology': Topology
}
