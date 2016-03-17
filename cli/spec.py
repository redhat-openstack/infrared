import ConfigParser
import os

import yaml
import yamlordereddictloader

import clg
from cli import exceptions
from cli import utils

SPEC_EXTENSION = '.spec'
BUILTINS_REPLACEMENT = {
    '__DEFAULT__': "default"
}

TRIM_PARAMS = ['default', 'required']


def cfg_file_to_dict(file_path):
    """
    Creates a dictionary based on given configuration file.

    :param file_path: Path to configuration file.
    :return: dict based on a provided configuration file.
    """
    config = ConfigParser.ConfigParser()
    with open(file_path) as fd:
        config.readfp(fd)

    res_dict = {}
    for section in config.sections():
        res_dict[section] = {}
        for option, value in config.items(section):
            # todo(obaranov) checking if value is list (for extra-vars).
            # rework that check to be more beautiful later.
            if value.startswith('[') and value.endswith(']'):
                value = eval(str(value))
            res_dict[section][option] = value

        res_dict[section].pop('__name__', None)

    return res_dict


def parse_args(app_settings_dir, args=None):
    """
    Looks for all the specs for specified app
    and parses the commandline input arguments accordingly.

    Trim clg spec from customized input and modify help data.

    :param app_settings_dir: path to the base directory holding the
        application's settings. App can be provisioner\installer\tester
        and the path would be: settings/<app_name>/
    :param args: additional arguments to pass to the clg.
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
clg.TYPES.update({'IniFile': cfg_file_to_dict})
