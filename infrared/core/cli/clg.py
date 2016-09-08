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

from infrared.core.utils import logger, utils, exceptions

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


class SpecParser(object):
    """
    Parses the input arguments from different sources (cli, file, env)
    """

    @classmethod
    def from_folder(cls, settings_folders,
                    app_name,
                    app_subfolder="",
                    user_dict=None, file_ext='spec', subparser=None):
        """
        Reads spec file from the settings folder and generate Spec object.
        :param settings_folders: the main settings folder
        :param app_subfolder: the application subfolder
            (provisioner/installer/tester)
        :param: user_dict: the user defined spec dictionary which will be added
            to the resulting spec
        :param file_ext: the spec file extension.
        :return: the Spec instance.
        """
        # look for common specs in the main of the settings file

        spec_files = []
        for settings_folder in settings_folders:
            spec_files.extend(
                glob.glob('./' + settings_folder + '/*' + file_ext))

            # look for all the spec files for an app
            main_folder = os.path.join(settings_folder, app_subfolder)

            for main, _, files in os.walk(main_folder):
                for a_file in files:
                    if a_file.endswith(file_ext):
                        full_path = os.path.join(main, a_file)
                        if full_path not in spec_files:
                            spec_files.append(full_path)

        return cls.from_files(settings_folders, app_name, app_subfolder,
                              user_dict, subparser, *spec_files)

    @classmethod
    def from_files(cls, settings_folders, app_name, app_subfolder,
                   user_dict, subparser, *spec_files):
        """
        Reads specs files and constructs the parser instance
        """
        if user_dict is None:
            user_dict = {}
        result = user_dict
        for spec_file in spec_files:
            with open(spec_file) as stream:
                spec = yaml.load(stream)
                utils.dict_merge(
                    result,
                    spec,
                    utils.ConflictResolver.unique_append_list_resolver)

        return SpecParser(
            result, settings_folders, app_name, app_subfolder, subparser)

    def __init__(self, spec_dict, settings_folders,
                 app_name, app_subfolder, subparser):
        self.app_name = app_name
        self.app_subfolder = app_subfolder
        self.settings_folders = settings_folders
        self.subparser = subparser

        # inject name to the spec_dict to handle it as regular subparser
        spec_dict['name'] = app_name
        self.spec_helper = SpecDictHelper(spec_dict)

        # create parser
        self.parser = CliParser.create_parser(self, subparsers=subparser)

    def add_shared_groups(self, list_of_groups):
        """
        Adds the user defined shared groups
        :param list_of_groups:  the list of group dict's

        """
        shared_groups = self.spec_helper.spec_dict.get('shared_groups', [])
        shared_groups.expand(list_of_groups)
        self.spec_helper.spec_dict['shared_groups'] = shared_groups

    def _get_defaults(self, default_getter_func):
        """
        Gets the defaults value from env, cli or ini file.

        The default_getter_func will be called for all the available options
        in spec file.
        """

        result = collections.defaultdict(dict)
        for parser, option in self.spec_helper.iterate_option_specs():
            default_value = default_getter_func(option)
            if default_value is not None:
                sub = parser['name']
                result[sub][option['name']] = default_value

        return result

    def get_env_defaults(self):
        """
        Gets the argument's defaults values from the environment.
        """

        def env_getter(option):
            """
            The getter function to retrieve the env variable for argument.
            """
            env_name = option['name'].replace('-', '_').upper()
            return os.environ.get(env_name, None)

        env_vars = self._get_defaults(env_getter)

        # convert arguments to correct type
        for parser_name, parser_dict in env_vars.items():
            self._convert_non_cli_args(parser_name, parser_dict)
        return env_vars

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

        file_result = {}
        for (parser_name, parser_dict, arg_name, arg_value,
             option_spec) in self._iterate_received_arguments(cli_args):
            file_result[parser_name] = file_result.get(parser_name, {})
            if option_spec and option_spec.get(
                    'action', '') == 'read-config':
                # we have config option. saving it.
                self._convert_non_cli_args(
                    parser_name, parser_dict[arg_name])
                utils.dict_merge(
                    file_result[parser_name],
                    parser_dict[arg_name])
                # remove from cli args
                parser_dict.pop(arg_name)

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
        for (parser_name, parser_dict, arg_name, arg_value,
             option_spec) in self._iterate_received_arguments(cli_args):
            if option_spec and option_spec.get(
                    'action', '') == 'generate-config':
                options_to_save = \
                    self.spec_helper.get_parser_option_specs(parser_name)
                out_config = ConfigParser.ConfigParser(allow_no_value=True)

                if os.path.exists(arg_value):
                    # todo(obaranov) comments from other section will be
                    # removed.
                    out_config.read(arg_value)

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
                with open(arg_value, 'w') as configfile:  # save
                    out_config.write(configfile)
                file_generated = True

        return file_generated

    def resolve_custom_types(self, args):
        """
        Transforms the arguments with custom types
        :param args: the list of received arguments.
        """
        for parser_name, parser_dict in args.items():
            spec_complex_options = [opt for opt in
                                    self.spec_helper.get_parser_option_specs(
                                        parser_name) if
                                    opt.get('type', None) in COMPLEX_TYPES]
            for spec_option in spec_complex_options:
                option_name = spec_option['name']
                if option_name in parser_dict:
                    # we have custom type to resolve
                    type_name = spec_option['type']
                    option_value = parser_dict[option_name]
                    action = self.create_custom_type(
                        parser_name,
                        type_name,
                        option_name)

                    # resolving value
                    parser_dict[option_name] = action.resolve(option_value)

    def create_custom_type(self, subcommand, type_name, option_name):
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
                "Unknown custom type: {}".format(type_name))
        return complex_action(
            option_name,
            self.settings_folders,
            self.app_name,
            self.app_subfolder,
            subcommand)

    def parse_args(self, arg_parser):
        """
        Parses all the arguments (cli, file, env) and returns two dicts:
            * command arguments dict (arguments to control the IR logic)
            * nested arguments dict (arguments to pass to the playbooks)
        """

        spec_defaults = self.get_spec_defaults()
        env_defaults = self.get_env_defaults()
        cli_args, unknown_args = CliParser.parse_args(
            self, arg_parser=arg_parser)

        file_args = self.get_config_file_args(cli_args)

        # generate config file and exit
        if self.generate_config_file(cli_args, spec_defaults):
            LOG.warning("Config file has been generated. Exiting.")
            return None

        # print warnings when something was overridden from non-cli source.
        self.validate_arg_sources(
            cli_args,
            env_defaults,
            file_args,
            spec_defaults)

        # todo(obaranov) Pass all the unknown arguments to the ansible
        # For now just raise exception
        if unknown_args:
            raise exceptions.IRUnrecognizedOptionsException(unknown_args)

        # merge defaults into one
        utils.dict_merge(spec_defaults, env_defaults)
        # now filter defaults to have only parser defined in cli
        defaults = {key: spec_defaults[key] for key in cli_args.keys() if
                    key in spec_defaults}

        # copy cli args with the same name to all parser groups
        self._merge_duplicated_cli_args(cli_args)
        self._merge_duplicated_cli_args(file_args)

        utils.dict_merge(defaults, file_args)
        utils.dict_merge(defaults, cli_args)
        self.validate_requires_args(defaults)

        # now resolve complex types.
        self.resolve_custom_types(defaults)
        nested, control = self.get_nested_and_control_args(defaults)
        return nested, control, unknown_args

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

        silent_args = self.get_silent_args(args)

        def validate_parser(parser_name, expected_options, parser_args):
            result = collections.defaultdict(list)
            condition_req_args = self._get_conditionally_required_args(
                parser_name, expected_options, args)

            for option in expected_options:
                name = option['name']

                # check required options.
                if (option.get('required', False) and
                        name not in parser_args or
                        option['name'] in condition_req_args) and \
                        name not in silent_args:
                    result[parser_name].append(name)

            return result

        res = {}
        for command_data in self.spec_helper.iterate_parsers():
            cmd_name = command_data['name']
            if cmd_name in args:
                utils.dict_merge(
                    res,
                    validate_parser(
                        cmd_name,
                        self.spec_helper.get_parser_option_specs(cmd_name),
                        args[cmd_name]))

        missing_args = {cmd_name: args
                        for cmd_name, args in res.items() if len(args) > 0}
        if missing_args:
            raise exceptions.IRRequiredArgsMissingException(missing_args)

    def get_silent_args(self, args):
        """
        Gets the list of options names that should silent'ed
        :param args: The received arguments.
        """
        silent_args_names = []
        for (parser_name, parser_dict, arg_name, arg_value,
             arg_spec) in self._iterate_received_arguments(args):
            if arg_spec and 'silent' in arg_spec and \
                self.spec_helper.get_option_state(
                    parser_name,
                    arg_name,
                    args) == OptionState.IS_SET:
                silent_args_names.extend(arg_spec['silent'])

        return list(set(silent_args_names))

    def get_nested_and_control_args(self, args):
        """
        Constructs control and nested args.

        Controls arguments control the IR behavior. These arguments
            will not be put into the spec yml file

        Nested arguments are used by the Ansible playbooks and will be put
            into the spec yml file.
        :param args: the collected list of args.
        :return: The pair of flat dicts (control_args, nested_args)
        """
        # returns flat dicts
        nested = {}
        control_args = {}
        for (parser_name, parser_dict, arg_name, arg_value,
             arg_spec) in self._iterate_received_arguments(args):
            if arg_spec and \
                    arg_spec.get('type', None) and \
                    arg_spec['type'] in [ctype_name for
                                         ctype_name, klass in
                                         COMPLEX_TYPES.items() if
                                         klass.is_nested]:
                if arg_name in nested:
                    LOG.warning(
                        "Duplicated nested argument found:'{}'. "
                        "Using old value: '{}'".format(
                            arg_name, nested[arg_name]))
                else:
                    nested[arg_name] = arg_value
            else:
                if arg_name in control_args:
                    LOG.warning(
                        "Duplicated control argument found: '{}'. Using "
                        "old value: '{}'".format(
                            arg_name, control_args[arg_name]))
                else:
                    control_args[arg_name] = arg_value

        return nested, control_args

    def _iterate_received_arguments(self, args):
        """
        Helper method to iterate over all the received arguments
        """
        for spec_parser in self.spec_helper.iterate_parsers():
            if spec_parser['name'] in args:
                parser_dict = args[spec_parser['name']]
                for arg_name, arg_val in parser_dict.items():
                    arg_spec = self.spec_helper.get_option_spec(
                        spec_parser['name'], arg_name)
                    yield (spec_parser['name'], parser_dict,
                           arg_name, arg_val, arg_spec)

    def _convert_non_cli_args(self, parser_name, values_dict):
        """
       Converts arguments to correct types by modifying values_dict param.

        By default all the values are strings.

       :param parser_name: The command name, e.g. main, virsh, ospd, etc
       :param values_dict: The dict of with arguments
       """
        for opt_name, opt_value in values_dict.items():
            file_option_spec = self.spec_helper.get_option_spec(
                parser_name, opt_name)
            if file_option_spec.get('type', None) in ['int', ] or \
                    file_option_spec.get('action', None) in ['count', ]:
                values_dict[opt_name] = int(opt_value)

    def _merge_duplicated_cli_args(self, cli_args):
        """
        Merge duplicated arguments to all the parsers

        This is need to handle args which belongs to several parsers,
        for example, verbose, inventory
        """
        for (parser_name, parser_dict, arg_name, arg_value,
             arg_spec) in self._iterate_received_arguments(cli_args):
            for parser_name2, parser_dict2 in cli_args.items():
                if parser_name != parser_name2 and parser_name2 and arg_name \
                        not in parser_dict2:
                    if self.spec_helper.get_option_spec(parser_name2,
                                                        arg_name):
                        parser_dict2[arg_name] = arg_value


class SpecDictHelper(object):
    """
    Controls the spec dicts and provides useful methods to get spec info.
    """

    def __init__(self, spec_dict):
        self.spec_dict = spec_dict
        # make structure of the dict flat
        # 1. handle include_groups directive in main parser
        parser_dict = self.spec_dict
        self._include_groups(parser_dict)
        # 2. Include groups for all subparsers
        for subparser_name, subparser_dict in parser_dict.get(
                'subparsers', {}).items():
            self._include_groups(subparser_dict)

    def iterate_parsers(self):
        """
        Iterates over the main parsers and subparser
        """
        yield self.spec_dict
        for subparser_name, subparser_dict in self.spec_dict.get(
                'subparsers', {}).items():
            yield dict(name=subparser_name, **subparser_dict)

    def iterate_option_specs(self):
        """
        Iterates over all the option specs.

        Returns pair of parser and option on every iteration.
        """
        for parser in self.iterate_parsers():
            for spec_option in self._get_all_options_spec(parser):
                yield parser, spec_option

    def _get_all_options_spec(self, parser_dict):
        """
        Gets all the options specification as the list of dicts
        """
        result = []
        for group in parser_dict.get('groups', []):
            for option_name, option_dict in group.get('options', {}).items():
                result.append(dict(name=option_name, **option_dict))

        for option_name, option_dict in parser_dict.get('options', {}).items():
            result.append(dict(name=option_name, **option_dict))

        return result

    def get_parser_option_specs(self, command_name):
        """
        Gets all the options for the specified command (main, virsh, ospd, etc)
        :param command_name: the command name
        :return: the list of all command options
        """
        options = []
        for parser in self.iterate_parsers():
            if parser['name'] == command_name:
                options = self._get_all_options_spec(parser)
                break
        return options

    def get_option_spec(self, command_name, argument_name):
        """
        Gets the specification for the specified option name
        """
        options = self.get_parser_option_specs(command_name)
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

    def _include_groups(self, parser_dict):
        """
        Resolves the include dict directive in the spec files.
        """
        for group in parser_dict.get('include_groups', []):
            # ensure we have that group
            grp_dict = next(
                (grp for grp in self.spec_dict.get('shared_groups', [])
                 if grp['title'] == group),
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
                description=parser_dict.get('description', ''),
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
