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

    res_args, subcommand_opts = _get_command_line_args(args, config,
                                                       module_name)

    # get the default values
    command_args = subcommand_opts[res_args['command0']]
    defaults = {k: v.get('default', None)
                for k, v in command_args.iteritems()}

    # generate config file if required
    if res_args.get('generate-conf-file', None):
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

    # override defaults with env variables
    for arg_name, arg_value in res_args.iteritems():
        upper_arg_name = arg_name.upper()
        if arg_value is None and upper_arg_name in os.environ:
            defaults[arg_name] = os.getenv(upper_arg_name)

    # override defaults with the ini file args
    if 'from-file' in res_args:
        file_args = res_args['from-file']
        if file_args is not None and res_args['command0'] in file_args:
            defaults = utils.dict_merge(
                file_args[res_args['command0']],
                defaults,
                conflict_resolver=utils.ConflictResolver.none_resolver)

    # replace defaults with cli
    utils.dict_merge(res_args, defaults,
                     conflict_resolver=utils.ConflictResolver.none_resolver)

    # check if we have all the required arguments defined at the end of merge
    unset_args = []
    only_args = []
    for arg_name, arg_param in command_args.iteritems():
        if 'required' in arg_param and \
                arg_param['required'] and \
                res_args.get(arg_name, None) is None:
            unset_args.append(arg_name)
        if 'requires_only' in arg_param:
            only_args.extend(arg_param['requires_only'])
    if len(only_args) > 0:
        intersection = set(unset_args).intersection(set(only_args))
        if len(intersection) > 0:
            raise exceptions.IRConfigurationException(
                "Required only input arguments {} are not set!".format(
                    intersection))
    elif len(unset_args) > 0:
        raise exceptions.IRConfigurationException(
            "Required input arguments {} are not set!".format(
                unset_args))
    return res_args


def _get_command_line_args(args, config, module_name):
    """
    Gets the arguments values from the command line.
    """
    clg_options, global_opts, subcommand_opts = \
        _load_spec_as_dict(module_name, config)
    cmd = clg.CommandLine(clg_options)
    res_args = vars(cmd.parse(args))
    return res_args, subcommand_opts


def _load_spec_as_dict(module_name, config):
    """
    Loads the spec file as dict.

    Returns tuple:
        dict of options and groups for clg
        dict of options without subcommands
        dict of options for subcommands
    """
    clg_options = _get_specs(module_name, config)
    global_options, subcommands_options = _process_options(clg_options)
    return clg_options, global_options, subcommands_options


def _process_options(spec_dict, lookup=False, trim=False):
    """
    Goes through all the spec options modifies them by removing
     some options parameters (like defaults)

    :param spec_dict: the dictionary with key obtained from spec file
    :param lookup: specifies whether the options lookup is required.
    :param trim: specifies whether the certain option
        parameters should be removed
    """
    global_options = {}
    subcommand_options = {}
    _process_flat_options(global_options, spec_dict, lookup, trim)
    _process_groups_options(global_options, spec_dict, lookup, trim)
    # collect sub parser global_options
    if 'subparsers' in spec_dict:
        for subparser_name, params in spec_dict['subparsers'].iteritems():
            subcommand_options[subparser_name], _ = _process_options(
                params, lookup=True, trim=True)

    return global_options, subcommand_options


def _process_groups_options(options, spec_dict, lookup, trim):
    """
    Gets the dict of options nested within the spec groups

    :param options:  the current list of options
    :param spec_dict: the dictionary to look for new group options.
    :param lookup: specifies whether the options lookup is required.
    :param trim: specifies whether the certain option
        parameters should be removed
    """
    if 'groups' in spec_dict:
        for group in spec_dict['groups']:
            _process_flat_options(options, group, lookup, trim)


def _process_flat_options(options, spec_dict, lookup, trim):
    """
    Gest the dict of options listed in the spec of group.

    This method will also remove some methods and will replace
     __<value>__ pattens in the option properties (e.g. __default__, __FILE__)

    :param options:  the current list of options
    :param spec_dict: the dictionary to look for new options.
    :param lookup: specifies whether the options lookup is required.
    :param trim: specifies whether the certain option
        parameters should be removed
    """
    if 'options' in spec_dict:
        for opt_name, opt_params in spec_dict['options'].iteritems():
            if lookup:
                _lookup_option(opt_name, opt_params)

            # get a parameters copy with all the keys.
            options[opt_name] = dict(opt_params)

            if trim:
                _trim_option(opt_name, opt_params)


def _lookup_option(opt_name, opt_params):
    """
    Modifies existing option parameters by replaceing ___*___ patterns
      and inserting default values into the help.
    :param opt_name: the option name to process
    :param opt_params: the dictionary of the option parameters
        (help, type, default, etc)
    """

    # first check __*__ pattern
    for opt_param_name, param_value in opt_params.iteritems():
        for lookup_string, lookup_key in LOOKUP_DICT.iteritems():
            if lookup_string in str(param_value):
                opt_params[opt_param_name] = \
                    param_value.replace(lookup_string, str(opt_params.get(
                        lookup_key, lookup_string)))

    # insert default value into help.
    if 'help' in opt_params and 'default' in opt_params:
        opt_params['help'] += " | Default value: {}".format(
            opt_params['default'])


def _trim_option(opt_name, opt_params):
    """
    Removes the defined option parameters.
    :param opt_name: the option name to process
    :param opt_params: the dictionary of the option parameters
        (help, type, default, etc)
    """
    for opt_param_name, param_value in opt_params.iteritems():
        if opt_param_name in TRIM_PARAMS:
            opt_params.pop(opt_param_name, None)


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
