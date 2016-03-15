import ConfigParser
import os
import yaml
import yamlordereddictloader

import clg
from cli import exceptions
from cli import utils

SPEC_EXTENSION = '.spec'
LOOKUP_DICT = {
    '__DEFAULT__': "default"
}

TRIM_PARAMS = ['default', 'required', 'requires_only']


def cfg_file_to_dict(value):
    """
    The custom type for clg spec
    :param value: the argument value.
    :return: dict based on a provided ini file.
    """
    config = ConfigParser.ConfigParser()
    with open(value) as fd:
        config.readfp(fd)

    res_dict = {}
    for section in config.sections():
        res_dict[section] = {}
        for option, value in config.items(section):
            value = utils.string_to_list(value, append_to_list=False)
            res_dict[section][option] = value

        res_dict[section].pop('__name__', None)

    return res_dict


def parse_args(module_name, config, args=None):
    """
    Looks for all the specs for specified module
    and parses the commandline input arguments accordingly.

    :param module_name: the module name: installer|provisioner|tester
    :param config: the infrared configuration file
    :param args: additional arguments to pass to the clg.
    """

    # get the options for clg module.
    clg_options = _get_specs(module_name, config)

    # get the command options as is with all the fields from yaml
    # this also trims some custom fields from options to pas to clg.
    subparser_options = _get_subparser_options(clg_options)
    cmd = clg.CommandLine(clg_options)
    res_args = vars(cmd.parse(args))

    override_default_values(res_args, subparser_options)
    return res_args


def override_default_values(res_args, subparser_options):
    """
    Collects argumetns values from the different sources and
    :param res_args: the list of command line arguments with values
    :param subcommand_opts: the subcommand spec options
    """
    # get the default values
    command_args = subparser_options[res_args['command0']]
    defaults = {option: attributes['default']
                for option, attributes in command_args.iteritems()
                if 'default' in attributes}

    # generate config file if required
    if res_args.get('generate-conf-file', None):
        _generate_config_file(defaults, res_args)
    else:
        # override defaults with env variables
        _replace_with_env_arguments(defaults, res_args)

        # override defaults with the ini file args
        _replace_with_ini_arguments(defaults, res_args)

        # replace defaults with cli
        utils.dict_merge(
            res_args,
            defaults,
            conflict_resolver=utils.ConflictResolver.none_resolver)

        _check_required_arguments(command_args, res_args)


def _check_required_arguments(command_args, res_args):
    """
    Verify all the required arguments are set.
    :param command_args: the dict with command spec options
    :param res_args: the current command line arguments value
    """
    unset_args = []
    only_args = []
    for arg_name, arg_param in command_args.iteritems():
        if arg_param.get('required', None) and \
                        res_args.get(arg_name, None) is None:
            unset_args.append(arg_name)
        if 'requires_only' in arg_param:
            only_args.extend(arg_param['requires_only'])
    if only_args:
        intersection = set(unset_args).intersection(set(only_args))
        if intersection:
            raise exceptions.IRConfigurationException(
                "Required only input arguments {} are not set!".format(
                    intersection))
    elif unset_args:
        raise exceptions.IRConfigurationException(
            "Required input arguments {} are not set!".format(
                unset_args))


def _replace_with_ini_arguments(defaults, res_args):
    """
    Replaces the default arguments values with the arguments from ini file.
    :param defaults: the default arguments values.
    :param res_args: the current command line arguments value
    """
    if 'from-file' in res_args:
        file_args = res_args['from-file']
        if file_args is not None and res_args['command0'] in file_args:
            utils.dict_merge(
                file_args[res_args['command0']],
                defaults,
                conflict_resolver=utils.ConflictResolver.none_resolver)
            defaults.update(file_args[res_args['command0']])


def _replace_with_env_arguments(defaults, res_args):
    """
    Replaces default variables with the variables from env.
    :param defaults: the default arguments values.
    :param res_args: the current command line arguments value
    """

    for arg_name, arg_value in res_args.iteritems():
        upper_arg_name = arg_name.upper()
        if arg_value is None and upper_arg_name in os.environ:
            defaults[arg_name] = os.getenv(upper_arg_name)


def _generate_config_file(defaults, res_args):
    """
    Generates config file

    :param defaults: the default arguments values.
    :param res_args: the current command line arguments value
    """
    try:
        file_name = res_args['generate-conf-file']
        out_config = ConfigParser.ConfigParser()

        section = res_args['command0']
        out_config.add_section(section)
        for opt, value in defaults.iteritems():
            if value is not None:
                out_config.set(section, opt, value)
        with open(file_name, 'w') as configfile:  # save
            out_config.write(configfile)
    except Exception as ex:
        raise exceptions.IRException(ex.message)


def _get_subparser_options(spec_dict, lookup=False, trim=False):
    """
    Goes through all the spec options modifies them by removing
     some options parameters (like defaults)

    :param spec_dict: the dictionary with key obtained from spec file
    :param lookup: specifies whether the options lookup is required.
    :param trim: specifies whether the certain option
        parameters should be removed
    """

    # collect sub parser parser_options
    options = {}
    if 'subparsers' in spec_dict:
        for subparser_name, params in spec_dict['subparsers'].iteritems():
            parser_options = _get_parser_options(params, lookup=True,
                                                 trim=True)
            group_options = _get_parser_group_options(
                params, lookup=True, trim=True)

            utils.dict_merge(parser_options, group_options)
            options[subparser_name] = parser_options

    return options


def _get_parser_group_options(spec_dict, lookup, trim):
    """
    Gets the dict of options nested within the spec groups

    :param spec_dict: the dictionary to look for new group options.
    :param lookup: specifies whether the options lookup is required.
    :param trim: specifies whether the certain option
        parameters should be removed
    """
    options = {}
    if 'groups' in spec_dict:
        for group in spec_dict['groups']:
            options.update(_get_parser_options(group, lookup, trim))
    return options


def _get_parser_options(spec_dict, lookup, trim):
    """
    Gets the dict of options listed in the spec of group.

    This method will also remove some methods and will replace
     __<value>__ pattens in the option properties (e.g. __default__, __FILE__)

    :param spec_dict: the dictionary to look for new options.
    :param lookup: specifies whether the options lookup is required.
    :param trim: specifies whether the certain option
        parameters should be removed
    """
    options = {}
    if 'options' in spec_dict:
        for opt_name, opt_params in spec_dict['options'].iteritems():
            _update_help(opt_params)
            if lookup:
                _replace_builtin(opt_params)

            # get a parameters copy with all the keys.
            options[opt_name] = dict(opt_params)

            if trim:
                _trim_option(opt_params)
    return options


def _update_help(opt_params):
    """
    Update the help by inserting default values if required.
    :param opt_params: the dictionary of the option parameters
        (help, type, default, etc)
    """
    # insert default value into help.
    if 'help' in opt_params and 'default' in opt_params \
            and '__DEFAULT__' not in opt_params['help']:
        opt_params['help'] += " | Default value: {}".format(
            opt_params['default'])


def _replace_builtin(opt_params):
    """
    Modifies existing option parameters by replaceing ___*___ patterns
    :param opt_params: the dictionary of the option parameters
        (help, type, default, etc)
    """

    # check __*__ pattern
    for opt_param_name, param_value in opt_params.iteritems():
        for lookup_string, lookup_key in LOOKUP_DICT.iteritems():
            if lookup_string in str(param_value):
                opt_params[opt_param_name] = \
                    param_value.replace(lookup_string, str(opt_params.get(
                        lookup_key, lookup_string)))


def _trim_option(opt_params):
    """
    Removes the defined option parameters.
    :param opt_params: the dictionary of the option parameters
        (help, type, default, etc)
    """
    for trim_param in TRIM_PARAMS:
        opt_params.pop(trim_param, None)


def _get_specs(module_name, config):
    """
    Gets specs files as a dict from settings/<module_name> folder.
    :param module_name: the module name: installer|provisioner|tester
    :param: config: the infrared configuration.
    """
    res = {}
    root_dir = utils.validate_settings_dir(
        config.get('defaults', 'settings'))
    if module_name:
        root_dir = os.path.join(root_dir, module_name)

    sepc_files = []
    for root, _, files in os.walk(root_dir):
        sepc_files.extend([os.path.join(root, a_file) for a_file in files
                           if a_file.endswith(SPEC_EXTENSION)])

    for spec_file in sepc_files:
        with open(spec_file) as fd:
            spec = yaml.load(fd, Loader=yamlordereddictloader.Loader)
        utils.dict_merge(res, spec)
    return res
