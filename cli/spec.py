import clg
import ConfigParser
import os
import sys
import yaml
import yamlordereddictloader

from cli import exceptions
from cli import utils

SPEC_EXTENSION = '.spec'
LOOKUP_DICT = {
    '__DEFAULT__': "default"
}

TRIM_PARAMS = ['default', 'required']


def IniFileType(value):
    """
    The custom type for clg spec
    :param value: the argument value.
    :return: dict based on a provided ini file.
    """
    _config = ConfigParser.ConfigParser()
    _config.read(value)

    d = dict(_config._sections)
    for k in d:
        d[k] = dict(_config._defaults, **d[k])
        for key, value in d[k].iteritems():
            # check if we have lists
            value = utils.string_to_list(value, append_to_list=False)
            d[k][key] = value
        d[k].pop('__name__', None)

    return d


def parse_args(module_name, config, args=None):
    """
    Looks for all the specs for specified module
    and parses the commandline input arguments accordingly.

    :param module_name: the module name: installer|provisioner|tester
    """

    clg_options, global_opts, subcommand_opts = \
        __load_spec_as_dict(module_name, config)

    cmd = clg.CommandLine(clg_options)
    res_args = vars(cmd.parse(args))

    # get the default values
    command_args = subcommand_opts[res_args['command0']]
    defaults = {k: v.get('default', None)
                for k, v in command_args.iteritems()}

    # generate config file if required
    if res_args['generate-conf-file']:
        try:
            file_name = res_args['generate-conf-file']
            out_config = ConfigParser.ConfigParser()

            section = res_args['command0']
            out_config.add_section(section)
            for opt, value in defaults.iteritems():
                if value is not None:
                    out_config.set(section, opt, value)
            with open(file_name, 'w') as configfile:    # save
                out_config.write(configfile)
        except Exception as ex:
            raise exceptions.IRException(ex.message)
        finally:
            sys.exit(0)

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

    return res_args

# ***************************************************************
# private method
# ***************************************************************


def __load_spec_as_dict(module_name, config):
    """
    Loads the spec file as dict.

    Returns tuple:
        dict of options and groups for clg
        dict of options without subcommands
        dict of options for subcommands
    """
    clg_options = _get_specs(module_name, config)
    global_options, subcommands_options = __process_options(clg_options)
    return clg_options, global_options, subcommands_options


def __process_options(spec_dict, lookup=False, trim=False):
    """
    Goes through all the spec options modifies them by removing
     some options parameters (like defaults)
    """
    global_options = {}
    subcommand_options = {}
    __get_flat_options(global_options, spec_dict, lookup, trim)
    __get_groups_options(global_options, spec_dict, lookup, trim)
    # collect sub parser global_options
    if 'subparsers' in spec_dict:
        for subparser_name, params in spec_dict['subparsers'].iteritems():
            subcommand_options[subparser_name], _ = __process_options(
                params, lookup=True, trim=True)

    return global_options, subcommand_options


def __get_groups_options(options, spec_dict, lookup, trim):
    """
    Gets the dict of options nested within the spec groups
    """
    if 'groups' in spec_dict:
        for group in spec_dict['groups']:
            __get_flat_options(options, group, lookup, trim)


def __get_flat_options(options, spec_dict, lookup, trim):
    """
    Gest the dict of options listed in the spec of group.

    This method will also remove some methods and will replace
     __<value>__ pattens in the option properties (e.g. __default__, __FILE__)

    """
    if 'options' in spec_dict:
        for opt_name, opt_params in spec_dict['options'].iteritems():
            if lookup:
                __lookup_option(opt_name, opt_params)

            # get a parameters copy with all the keys.
            options[opt_name] = dict(opt_params)

            if trim:
                __trim_option(opt_name, opt_params)


def __lookup_option(opt_name, opt_params):
    """
    Modifies existing option parameters by replaceing ___*___ patterns
      and inserting default values into the help.
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


def __trim_option(opt_name, opt_params):
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
    """
    res = {}
    for spec_file in _get_all_specs(config, subfolder=module_name):
        spec = yaml.load(
            open(spec_file),
            Loader=yamlordereddictloader.Loader)
        utils.dict_merge(res, spec)
    return res


def _get_all_specs(config, subfolder=None):
    """
    Gets all the list of all spec files.
    """
    root_dir = utils.validate_settings_dir(
        config.get('defaults', 'settings'))
    if subfolder:
        root_dir = os.path.join(root_dir, subfolder)

    res = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in [f for f in filenames
                         if f.endswith(SPEC_EXTENSION)]:
            res.append(os.path.join(dirpath, filename))

    return res