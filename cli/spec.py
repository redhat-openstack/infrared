import ConfigParser
import os

import yaml
import yamlordereddictloader

import clg

from cli import exceptions
from cli import logger
from cli import utils


LOG = logger.LOG

SPEC_EXTENSION = '.spec'
BUILTINS_REPLACEMENT = {
    '__DEFAULT__': "default"
}

TRIM_PARAMS = ['default', 'required']


class ValueArgument(object):
    """
    Default argument type for InfraRed Spec
    Resolves "None" Types with priority defaults.
    """
    def __init__(self, value=None):
        self.value = value
        self.arg_name = None

    def resolve_value(self, arg_name, defaults=None):
        """
        Resolve the argument value with alternative input origins

        Search order:
            1. Given value from CLI parsing
            2. Environment variables:
                [Aa-Zz] -> [A-Z]
                "-" -> "_"
            3. defaults dict

        :param arg_name: argument name from clg
        :param defaults: dict containing default values.
        """
        defaults = defaults or {}
        self.arg_name = arg_name
        # override get default from env variables
        if self.value is None:
            self.value = os.getenv(self.arg_name.upper().replace("-", "_"))
        # override get default from conf file
        if self.value is None:
            self.value = defaults.get(self.arg_name)


class YamlFileArgument(ValueArgument):
    """
    YAML file input argument.
    Loads legal YAML from file.
    Will search for files in the settings directory before trying to resolve
        absolute path.

    For the argument name is "arg-name" and of subparser "SUBCOMMAND" of command
        "COMMAND", the default search path would be:

         settings_dir/COMMAND/SUBCOMMAND/arg/name/arg_value
    """

    def find_file(self, search_first):
        """Find yaml file. search default path first.

        :param search_first: default path to search first
        :returns: absolute path to yaml file
        """
        filename = self.value
        search_first = os.path.join(search_first,
                                    *self.arg_name.split("-"))

        filename = os.path.join(search_first, filename) if os.path.exists(
            os.path.join(search_first, filename)) else filename
        if os.path.exists(os.path.abspath(filename)):
            LOG.debug("Loading YAML file: %s" %
                      os.path.abspath(filename))
            path = os.path.abspath(filename)
        else:
            raise exceptions.IRFileNotFoundException(
                file_path=os.path.abspath(filename))
        with open(path) as yaml_file:
            self.value = yaml.load(yaml_file)


class IniFileArgument(object):
    """Creates a dictionary based on given configuration file."""

    def __init__(self, value):
        """Loads dict based on a provided configuration file.

        :param value: Path to configuration file.
        """

        _config = ConfigParser.ConfigParser()
        with open(value) as fd:
            _config.readfp(fd)

        res_dict = {}
        for section in _config.sections():
            res_dict[section] = {}
            for option, val in _config.items(section):
                # todo(obaranov) checking if val is list (for extra-vars).
                # rework that check to be more beautiful later.
                if val.startswith('[') and val.endswith(']'):
                    val = eval(str(val))
                res_dict[section][option] = val

            res_dict[section].pop('__name__', None)

        self.value = res_dict


def parse_args(app_settings_dir, args=None):
    """
    Looks for all the specs for specified app
    and parses the commandline input arguments accordingly.

    Trim clg spec from customized input and modify help data.

    :param app_settings_dir: path to the base directory holding the
        application's settings. App can be provisioner\installer\tester
        and the path would be: settings/<app_name>/
    :param args: the list of arguments used for directing the method to work
        on something other than CLI input (for example, in testing).
    """
    # Dict with the merging result of all app's specs
    app_specs = _get_specs(app_settings_dir)

    # Get the subparsers options as is with all the fields from app's specs.
    # This also trims some custom fields from options to pass to clg.
    subparsers_options = _get_subparsers_options(app_specs)

    # Pass trimmed spec to clg with modified help message
    cmd = clg.CommandLine(app_specs)
    clg_args = vars(cmd.parse(args))

    # Current sub-parser options
    sub_parser_options = subparsers_options.get(clg_args['command0'], {})

    override_default_values(clg_args, sub_parser_options)

    return clg_args


def override_default_values(clg_args, sub_parser_options):
    """
    Collects arguments values from the different sources and resolve values.

    Each argument value is resolved in the following priority:
    1. Explicitly provided from cmd-line
    2. Environment variable
    3. Provided configuration file.
    4. Spec defaults

    :param clg_args: Dictionary based on cmd-line args parsed by clg
    :param sub_parser_options: the sub-parser spec options
    """
    # Get the sub-parser's default values
    defaults = {option: attributes['default']
                for option, attributes in sub_parser_options.iteritems()
                if 'default' in attributes}

    # todo(yfried): move this outside
    # Generate config file if required
    if clg_args.get('generate-conf-file'):
        _generate_config_file(
            file_name=clg_args['generate-conf-file'],
            subcommand=clg_args['command0'],
            defaults=defaults)
    else:
        # Override defaults with env variables
        _replace_defaults_with_env_arguments(defaults, clg_args)

        # Override defaults with the ini file args
        _replace_with_ini_arguments(defaults, clg_args)

        # Replace defaults with cli
        utils.dict_merge(
            clg_args, defaults,
            conflict_resolver=utils.ConflictResolver.none_resolver)

        _check_required_arguments(sub_parser_options, clg_args)


def _check_required_arguments(command_args, clg_args):
    """
    Verify all the required arguments are set.

    :param command_args: the dict with command spec options
    :param clg_args: Dictionary based on cmd-line args parsed by clg
    """
    unset_args = []
    # only_args = []
    for option, attributes in command_args.iteritems():
        if attributes.get('required') and clg_args.get(option) is None:
            unset_args.append(option)
        # todo(yfried): revisit this in the future
        # if 'requires_only' in attributes:
        #     only_args.extend(attributes['requires_only'])

    # if only_args:
    #     intersection = set(unset_args).intersection(set(only_args))
    #     if intersection:
    #         raise exceptions.IRConfigurationException(
    #             "Missing mandatory arguments: {}".format(
    #                 list(intersection)))
    if unset_args:
        raise exceptions.IRConfigurationException(
            "Required input arguments {} are not set!".format(unset_args))


def _replace_with_ini_arguments(defaults, clg_args):
    """
    Replaces the default arguments values with the arguments from ini file.

    :param defaults: the default arguments values.
    :param clg_args: Dictionary based on cmd-line args parsed by clg
    """
    file_args = clg_args.get('from-file')
    if file_args is not None and clg_args['command0'] in file_args:
        utils.dict_merge(
            file_args[clg_args['command0']], defaults,
            conflict_resolver=utils.ConflictResolver.none_resolver)
        defaults.update(file_args[clg_args['command0']])


def _replace_defaults_with_env_arguments(defaults, args_dict):
    """
    Replaces default variables with the variables from env.

    :param defaults: the default arguments values.
    :param args_dict: the current command line arguments value
    """
    # TODO (aopincar): IR env vars should be more uniques
    for arg_name, arg_value in args_dict.iteritems():
        upper_arg_name = arg_name.upper()
        if arg_value is None and upper_arg_name in os.environ:
            defaults[arg_name] = os.getenv(upper_arg_name)


def _generate_config_file(file_name, subcommand, defaults):
    """
    Generates configuration file based on defaults from specs

    :param file_name: Name of the new configuration that will be generated.
    :param subcommand: The subparser for which the conf file is generated
    :param defaults: the default options values.
    """
    # TODO(yfried): Add required arguments to file
    # TODO (aopincar): try block is too wide
    # TODO (aopincar): if file_name exists, update it instead of overwrite it
    try:
        out_config = ConfigParser.ConfigParser()

        out_config.add_section(subcommand)
        for opt, value in defaults.iteritems():
            out_config.set(subcommand, opt, value)
        with open(file_name, 'w') as configfile:  # save
            out_config.write(configfile)
    except Exception as ex:
        raise exceptions.IRException(ex.message)


def _get_subparsers_options(spec_dict):
    """
    Goes through all the spec options and modifies them by removing some
    options parameters (like defaults)

    :param spec_dict: the dictionary with key obtained from spec files
    """
    # Collect sub parsers options
    options = {}
    for sub_parser, params in spec_dict.get('subparsers', {}).iteritems():
        parser_options = _get_parser_options(params)
        group_options = _get_parser_group_options(params)

        utils.dict_merge(parser_options, group_options)
        options[sub_parser] = parser_options

    return options


def _get_parser_group_options(spec_dict):
    """
    Gets the dict of options nested within the spec groups

    :param spec_dict: the dictionary to look for new group options.
    """
    options = {}
    for group in spec_dict.get('groups', {}):
        options.update(_get_parser_options(group))

    return options


def _get_parser_options(spec_dict):
    """
    Gets the dict of options listed in the spec of group.

    This method will also remove some methods and will replace
     __<value>__ pattens in the option properties (e.g. __default__, __FILE__)

    :param spec_dict: the dictionary to look for new options.
    """
    options_dict = {}
    for option, attributes in spec_dict.get('options', {}).iteritems():
        _add_default_to_option_help(attributes)
        _replace_builtin(attributes)

        # Get a parameters copy with all the keys.
        options_dict[option] = dict(attributes)

        _trim_option(attributes)

    return options_dict


def _add_default_to_option_help(option_attributes):
    """
    Update the help by inserting default values if required.

    :param option_attributes: dictionary with option attributes (help, type,
    default, etc)
    """
    # Insert default value into help.
    if all(attr in option_attributes for attr in ('help', 'default')) \
            and '__DEFAULT__' not in option_attributes['help']:
        option_attributes['help'] += " (default: {})".format(
            option_attributes['default'])


def _replace_builtin(option_attributes):
    """
    Modifies existing option parameters by replacing __*__ patterns

    :param option_attributes: dictionary with option attributes (help, type,
    default, etc)
    """
    # check __*__ pattern
    for attr_key, attr_value in option_attributes.iteritems():
        for builtin, replacement in BUILTINS_REPLACEMENT.iteritems():
            if builtin in str(attr_value):
                option_attributes[attr_key] = \
                    attr_value.replace(builtin, str(
                        option_attributes.get(replacement, builtin)))


def _trim_option(option_attributes):
    """
    Removes the defined option parameters.

    :param option_attributes: dictionary with option attributes (help, type,
    default, etc)
    """
    for trim_param in TRIM_PARAMS:
        option_attributes.pop(trim_param, None)


def _get_specs(app_settings_dir):
    """
    Load all  specs files from base settings directory.

    :param app_settings_dir: path to the base directory holding the
        application's settings. App can be provisioner\installer\tester
        and the path would be: settings/<app_name>/
    :return: dict: All spec files merged into a single dict.
    """
    if not os.path.exists(app_settings_dir):
        raise exceptions.IRFileNotFoundException(app_settings_dir)

    # Collect all app's spec
    spec_files = []
    for root, _, files in os.walk(app_settings_dir):
        spec_files.extend([os.path.join(root, a_file) for a_file in files
                           if a_file.endswith(SPEC_EXTENSION)])

    res = {}
    for spec_file in spec_files:
        # TODO (aopincar): print spec_file in debug mode
        with open(spec_file) as fd:
            spec = yaml.load(fd, Loader=yamlordereddictloader.Loader)
        # TODO (aopincar): preserve OrderedDict when merging?!?
        utils.dict_merge(res, spec)

    return res

# update clg types
clg.TYPES.update({'IniFile': IniFileArgument})
clg.TYPES.update({'Value': ValueArgument})
clg.TYPES.update({'YamlFile': YamlFileArgument})
