import collections
from six.moves import configparser
import yaml
import os

from infrared.core.utils import logger
from infrared.core.utils import dict_utils
from infrared.core.utils import exceptions
from infrared.core.cli.cli import CliParser
from infrared.core.cli.cli import COMPLEX_TYPES
from infrared.core.inspector import helper

LOG = logger.LOG


class SpecParser(object):
    """Parses input arguments from different sources (cli, answers file). """

    @classmethod
    def from_plugin(cls, subparser, plugin, base_groups):
        """Reads spec & vars from plugin and constructs the parser instance

        :param subparser: argparse.subparser to extend
        :param plugin: InfraredPlugin object
        :param base_groups: dict, included groups
        :return: SpecParser object based on given plugin spec & vars
        """

        spec_dict = base_groups or {}
        with open(plugin.spec) as stream:
            spec = yaml.load(stream) or {}
            dict_utils.dict_merge(
                base_groups,
                spec,
                dict_utils.ConflictResolver.unique_append_list_resolver)

        # The "try-excpet" block here is for adding spec file path if it
        # includes an unsupported option type
        try:
            return SpecParser(subparser, spec_dict, plugin.vars_dir,
                              plugin.defaults_dir, plugin.path)
        except exceptions.IRUnsupportedSpecOptionType as ex:
            ex.message += ' in file: {}'.format(plugin.spec)
            raise ex

    def __init__(self, subparser, spec_dict, vars_dir, defaults_dir,
                 plugin_path):
        """

        :param subparser: argparse.subparser to extend
        :param spec_dict: dict with CLI description
        :param vars_dir: Path to plugin's vars dir
        :param defaults_dir: Path to plugin's defaults dir
        """
        self.vars = vars_dir
        self.defaults = defaults_dir
        self.plugin_path = plugin_path
        self.spec_helper = helper.SpecDictHelper(spec_dict)

        # create parser
        self.parser = CliParser.create_parser(self, subparser)

    def add_shared_groups(self, list_of_groups):
        """Adds the user defined shared groups

        :param list_of_groups: list, of group dicts
        """
        shared_groups = self.spec_helper.spec_dict.get('shared_groups', [])
        shared_groups.expand(list_of_groups)
        self.spec_helper.spec_dict['shared_groups'] = shared_groups

    def _get_defaults(self, default_getter_func):
        """Resolve arguments' values from cli or answers file.

        :param default_getter_func: callable. will be called for all the
            available options in spec file.
        """

        result = collections.defaultdict(dict)
        for parser, option in self.spec_helper.iterate_option_specs():
            default_value = default_getter_func(option)
            if default_value is not None:
                sub = parser['name']
                result[sub][option['name']] = default_value

        return result

    def get_spec_defaults(self):
        """Resolve arguments' values from spec and other sources. """

        def spec_default_getter(option):
            """Getter function to retrieve the default value from spec.

            :param option: argument name
            """

            # first try to get environment variable with IR_ prefix
            default_value = SpecParser.get_env_option(option['name'])
            if default_value is not None:
                LOG.info(
                    "[environ] Loading '{0}' default value"
                    " '{1}' from the environment variable".format(
                        option['name'], default_value))
            elif option.get('default', None) is not None:
                default_value = option['default']
            elif option.get('action', None) in ['store_true']:
                default_value = False
            return default_value

        return self._get_defaults(spec_default_getter)

    @staticmethod
    def get_env_option(name):
        """ Try get """
        return os.environ.get('IR_' + name.upper().replace('-', '_'))

    def get_deprecated_args(self):
        """Returning dict with options which deprecate others. """

        result = collections.defaultdict(dict)
        for parser, option in self.spec_helper.iterate_option_specs():
            if option.get('deprecates') is not None:
                result[option.get('deprecates')] = option.get('name')

        return result

    def get_answers_file_args(self, cli_args):
        """Resolve arguments' values from answers INI file. """

        file_result = {}
        args_to_remove = []
        for (parser_name, parser_dict, arg_name, arg_value,
             option_spec) in self._iterate_received_arguments(cli_args):
            file_result[parser_name] = file_result.get(parser_name, {})
            if option_spec and option_spec.get(
                    'action', '') == 'read-answers':
                # we have config option. saving it.
                self._convert_non_cli_args(
                    parser_name, parser_dict[arg_name])
                dict_utils.dict_merge(
                    file_result[parser_name],
                    parser_dict[arg_name])
                # remove from cli args
                args_to_remove.append((parser_name, arg_name))

        # remove parser dict outside loop to avoid iteration dict modification
        for parser_name, arg_name in args_to_remove:
            for spec_parser in self.spec_helper.iterate_parsers():
                if spec_parser['name'] in cli_args and spec_parser['name'] == parser_name:
                    parser_dict = cli_args[spec_parser['name']]
                    parser_dict.pop(arg_name)
                    break

        return file_result

    def generate_answers_file(self, cli_args, spec_defaults):
        """Generates answers INI file

        :param cli_args: list, cli arguments.
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
                str(value))

        file_generated = False

        # load generate answers file for all the parsers
        for (parser_name, parser_dict, arg_name, arg_value,
             option_spec) in self._iterate_received_arguments(cli_args):
            if option_spec and option_spec.get(
                    'action', '') == 'generate-answers':
                options_to_save = \
                    self.spec_helper.get_parser_option_specs(parser_name)
                out_answers = configparser.ConfigParser(allow_no_value=True)

                if not out_answers.has_section(parser_name):
                    out_answers.add_section(parser_name)

                for option in options_to_save:
                    opt_name = option['name']
                    if opt_name in parser_dict:
                        put_option(
                            out_answers,
                            parser_name,
                            opt_name,
                            parser_dict[opt_name])
                    elif opt_name in spec_defaults[parser_name]:
                        put_option(
                            out_answers,
                            parser_name,
                            opt_name,
                            spec_defaults[parser_name][opt_name])
                    elif option.get('required', False):
                        put_option(
                            out_answers,
                            parser_name,
                            '# ' + opt_name,
                            "Required argument. "
                            "Edit with one of the allowed values OR "
                            "override with "
                            "CLI: --{}=<option>".format(opt_name))

                # write to file
                with open(arg_value, 'w') as answers_file:
                    out_answers.write(answers_file)
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
                    action = self.create_complex_argumet_type(
                        parser_name,
                        type_name,
                        option_name,
                        spec_option)

                    # resolving value
                    parser_dict[option_name] = action.resolve(option_value)

    def create_complex_argumet_type(self, subcommand, type_name, option_name,
                                    spec_option):
        """Build the complex argument type

        :param subcommand: the command name
        :param type_name: the complex type name
        :param option_name: the option name
        :param spec_option: option's specifications
        :return: the complex type instance
        """
        complex_action = COMPLEX_TYPES.get(
            type_name, None)
        if complex_action is None:
            raise exceptions.SpecParserException(
                "Unknown complex type: {}".format(type_name))
        return complex_action(
            option_name,
            (self.vars, self.defaults, self.plugin_path),
            subcommand,
            spec_option)

    def parse_args(self, arg_parser, args=None):
        """Parses all the arguments (cli, answers file)

        :return: None, if ``--generate-answers-file`` in arg_arg_parser
        :return: (dict, dict):
            * command arguments dict (arguments to control the IR logic)
            * nested arguments dict (arguments to pass to the playbooks)
        """

        spec_defaults = self.get_spec_defaults()
        cli_args = CliParser.parse_cli_input(arg_parser, args)

        file_args = self.get_answers_file_args(cli_args)

        # generate answers file and exit
        if self.generate_answers_file(cli_args, spec_defaults):
            LOG.warning("Answers file generated. Exiting.")

        # print warnings when something was overridden from non-cli source.
        self.validate_arg_sources(cli_args, file_args,
                                  spec_defaults)

        # print warnings for deprecated
        self.validate_arg_deprecation(cli_args, file_args)

        # now filter defaults to have only parser defined in cli
        defaults = dict((key, spec_defaults[key])
                        for key in cli_args.keys() if
                        key in spec_defaults)

        # copy cli args with the same name to all parser groups
        self._merge_duplicated_cli_args(cli_args)
        self._merge_duplicated_cli_args(file_args)

        dict_utils.dict_merge(defaults, file_args)
        dict_utils.dict_merge(defaults, cli_args)
        self.validate_requires_args(defaults)
        self.validate_length_args(defaults)
        self.validate_choices_args(defaults)
        self.validate_min_max_args(defaults)

        # now resolve complex types.
        self.resolve_custom_types(defaults)
        nested, control = self.get_nested_and_control_args(defaults)
        return nested, control

    def validate_arg_deprecation(self, cli_args, answer_file_args):
        """Validates and prints the deprecated arguments.

        :param cli_args: the dict of arguments from cli
        :param answer_file_args:  the dict of arguments from files
        """

        for deprecated, deprecates in self.get_deprecated_args().items():
            for input_args in (answer_file_args.items(), cli_args.items()):
                for command, command_dict in input_args:
                    if deprecated in command_dict:
                        if deprecates in command_dict:
                            raise exceptions.IRDeprecationException(
                                "[{}] Argument '{}' deprecates '{}',"
                                " please use only the new one.".format(
                                    command, deprecated, deprecates))

                        if deprecated in answer_file_args[command]:
                            answer_file_args[command][deprecates] = \
                                answer_file_args[command][deprecated]

                        if deprecated in cli_args[command]:
                            cli_args[command][deprecates] = \
                                cli_args[command][deprecated]

                        LOG.warning(
                            "[{}] Argument '{}' was deprecated,"
                            " please use '{}'.".format(
                                command, deprecated, deprecates))

    @staticmethod
    def validate_arg_sources(cli_args, answer_file_args, spec_defaults):
        """Validates and prints the arguments' source.

        :param cli_args: the dict of arguments from cli
        :param answer_file_args:  the dict of arguments from files
        :param spec_defaults:  the default values from spec files
        """

        def show_diff(diff, command_name, cmd_dict, source_name):
            if diff:
                for arg_name in diff:
                    value = cmd_dict[arg_name]
                    LOG.info(
                        "[{}] Argument '{}' was set to"
                        " '{}' from the {} source.".format(
                            command_name, arg_name, value, source_name))

        for command, command_dict in cli_args.items():
            file_dict = answer_file_args.get(command, {})
            file_diff = set(file_dict.keys()) - set(command_dict.keys())
            show_diff(file_diff, command, file_dict, 'answers file')

            def_dict = spec_defaults.get(command, {})
            default_diff = set(def_dict.keys()) - set(
                command_dict.keys()) - file_diff
            show_diff(default_diff, command, def_dict, 'spec defaults')

    def _get_conditionally_required_args(self, command_name, options_spec,
                                         args):
        """List arguments with ``required_when`` condition matched.

        :param command_name: the command name.
        :param options_spec:  the list of command spec options.
        :param args: the received input arguments
        :return: list, list of argument names with matched ``required_when``
            condition
        """
        opts_names = [option_spec['name'] for option_spec in options_spec]
        missing_args = []
        for option_spec in options_spec:
            option_results = []
            if option_spec and 'required_when' in option_spec:
                req_when_args = [option_spec['required_when']] \
                    if not type(option_spec['required_when']) is list \
                    else option_spec['required_when']

                # validate conditions
                for req_when_arg in req_when_args:
                    splited_args_list = req_when_arg.split()
                    for idx, req_arg in enumerate(splited_args_list):
                        if req_arg in opts_names:
                            splited_args_list[idx] = \
                                args.get(command_name, {}).get(req_arg.strip())
                        if splited_args_list[idx] is None:
                            option_results.append(False)
                            break
                        splited_args_list[idx] = str(splited_args_list[idx])
                        if not any(
                                (c in '<>=') for c in splited_args_list[idx]):
                            splited_args_list[idx] = "'{0}'".format(
                                yaml.load(splited_args_list[idx]))
                    else:
                        option_results.append(
                            eval(' '.join(splited_args_list)))
                if all(option_results) and \
                        self.spec_helper.get_option_state(
                            command_name,
                            option_spec['name'],
                            args) == helper.OptionState['NOT_SET']:
                    missing_args.append(option_spec['name'])
        return missing_args

    def validate_requires_args(self, args):
        """Check if all the required arguments have been provided. """

        silent_args = self.get_silent_args(args)

        def validate_parser(parser_name, expected_options, parser_args):
            """Helper method to resolve dict_merge. """

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
                dict_utils.dict_merge(
                    res,
                    validate_parser(
                        cmd_name,
                        self.spec_helper.get_parser_option_specs(cmd_name),
                        args[cmd_name]))

        missing_args = dict((cmd_name, args)
                            for cmd_name, args in res.items() if len(args) > 0)
        if missing_args:
            raise exceptions.IRRequiredArgsMissingException(missing_args)

    def validate_length_args(self, args):
        """ Check if value of arguments is not longer than length specified.

        :param args: The received arguments.
        """
        invalid_options = []
        for parser_name, parser_dict in args.items():
            for spec_option in \
                    self.spec_helper.get_parser_option_specs(parser_name):
                if 'length' not in spec_option:
                    # skip options that does not contain length
                    continue
                option_name = spec_option['name']
                if option_name in parser_dict:
                    # resolve length
                    length = spec_option['length']
                    option_value = parser_dict[option_name]
                    if len(option_value) > int(length):
                        # found invalid option, append to list of invalid opts
                        invalid_options.append((
                            option_name,
                            option_value,
                            length
                        ))
        if invalid_options:
            # raise exception with all arguments that exceed length
            raise exceptions.IRInvalidLengthException(invalid_options)

    def validate_choices_args(self, args):
        """Check if value of choice arguments is one of the available choices.

        :param args: The received arguments.
        """
        invalid_options = []
        for parser_name, parser_dict in args.items():
            for spec_option in \
                    self.spec_helper.get_parser_option_specs(parser_name):
                if 'choices' not in spec_option:
                    # skip options that does not contain choices
                    continue
                option_name = spec_option['name']
                if option_name in parser_dict:
                    # resolve choices
                    choices = spec_option['choices']
                    option_value = parser_dict[option_name]
                    if option_value not in choices:
                        # found invalid option, append to list of invalid opts
                        invalid_options.append((
                            option_name,
                            option_value,
                            choices
                        ))
        if invalid_options:
            # raise exception with all arguments that contains invalid choices
            raise exceptions.IRInvalidChoiceException(invalid_options)

    def validate_min_max_args(self, args):
        """Check if value of arguments is between minimum and maximum values.

        :param args: The received arguments.
        """
        invalid_options = []
        for parser_name, parser_dict in args.items():
            for spec_option in \
                    self.spec_helper.get_parser_option_specs(parser_name):
                if all([key not in spec_option
                        for key in ('maximum', 'minimum')]):
                    # skip options that does not contain minimum or maximum
                    continue
                option_name = spec_option['name']

                if option_name in parser_dict:
                    option_value = parser_dict[option_name]
                    min_value = spec_option.get('minimum')
                    max_value = spec_option.get('maximum')
                    # handle empty values in spec files which load as None
                    min_value = '' if 'minimum' in spec_option \
                                      and min_value is None else min_value
                    max_value = '' if 'maximum' in spec_option \
                                      and max_value is None else max_value

                    values = {
                        "value": option_value,
                        "maximum": max_value,
                        "minimum": min_value
                    }

                    # make sure that values are numbers
                    is_all_values_numbers = True
                    for name, num in values.items():
                        if num is not None \
                                and (isinstance(num, bool) or
                                     not isinstance(num, (int, float))):
                            invalid_options.append((
                                option_name,
                                name,
                                "number",
                                type(num).__name__
                            ))
                            is_all_values_numbers = False

                    if not is_all_values_numbers:
                        # don't continue to min max checks since some of the
                        # values are not numbers
                        continue

                    # check bigger than minimum
                    if min_value is not None and option_value < min_value:
                        invalid_options.append((
                            option_name,
                            "minimum",
                            min_value,
                            option_value
                        ))
                    # check smaller than maximum
                    if max_value is not None and option_value > max_value:
                        invalid_options.append((
                            option_name,
                            "maximum",
                            max_value,
                            option_value
                        ))

        if invalid_options:
            # raise exception with all arguments that contains invalid choices
            raise exceptions.IRInvalidMinMaxRangeException(invalid_options)

    def get_silent_args(self, args):
        """list of silenced argument

        :param args: The received arguments.
        :return: list, slienced argument names
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
        """Split input arguments to control nested.

        Controls arguments: control the IR behavior. These arguments
            will not be put into the spec yml file
        Nested arguments: are used by the Ansible playbooks and will be put
            into the spec yml file.

        :param args: the collected list of args.
        :return: (dict, dict): flat dicts (control_args, nested_args)
        """
        # returns flat dicts
        nested = {}
        control_args = {}
        for (parser_name, parser_dict, arg_name, arg_value,
             arg_spec) in self._iterate_received_arguments(args):
            if all([arg_spec, arg_spec.get('type', None),
                    arg_spec.get('type', None) in
                    [ctype_name for ctype_name, klass in
                     COMPLEX_TYPES.items() if klass.is_nested]
                    ]) or ('is_shared_group_option' not in arg_spec):
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
        """Iterator helper method over all the received arguments

        :return: yields tuple:
            (spec name, spec dict,
             argument name, argument value, argument spec)
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
        """Casts arguments to correct types by modifying values_dict param.

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
        """Merge duplicated arguments to all the parsers

        This is need to handle control args, shared among several parsers.
        for example, verbose, inventory
        """
        for (parser_name, parser_dict, arg_name, arg_value,
             arg_spec) in self._iterate_received_arguments(cli_args):
            for parser_name2, parser_dict2 in cli_args.items():
                if all([parser_name2, parser_name != parser_name2,
                        arg_name not in parser_dict2]):
                    if self.spec_helper.get_option_spec(parser_name2,
                                                        arg_name):
                        parser_dict2[arg_name] = arg_value
