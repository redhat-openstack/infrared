import os
import glob
import collections
import yaml
import ConfigParser

from infrared.core.utils import logger
from infrared.core.utils import utils
from infrared.core.utils import exceptions
from infrared.core.utils.exceptions import SpecParserException
from infrared.core.cli.cli import CliParser
from infrared.core.cli.cli import COMPLEX_TYPES
import helper


LOG = logger.LOG


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
                spec = yaml.load(stream) or {}
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
        self.spec_helper = helper.SpecDictHelper(spec_dict)

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

    @staticmethod
    def validate_arg_sources(cli_args, env_defaults, file_args,
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

    def _get_conditionally_required_args(self, command_name, options_spec, args):
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
                            option_spec['name'], args) == helper.OptionState['NOT_SET']:
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
                    args) == helper.OptionState['IS_SET']:
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
