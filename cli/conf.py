import ConfigParser

import sys

import clg
import os
import yaml
import yamlordereddictloader
from cli import exceptions
from cli import utils

DEFAULT_INI = 'default.ini'


def load_config_file():
    """Load config file order(ENV, CWD, USER HOME, SYSTEM).

    :return ConfigParser: config object
    """

    # create a parser with default path to InfraRed's main dir
    cwd_path = os.path.join(os.getcwd(), utils.IR_CONF_FILE)
    _config = ConfigParser.ConfigParser()

    env_path = os.getenv(utils.ENV_VAR_NAME, None)
    if env_path is not None:
        env_path = os.path.expanduser(env_path)
        if os.path.isdir(env_path):
            env_path = os.path.join(env_path, utils.IR_CONF_FILE)

    for path in (env_path, cwd_path, utils.USER_PATH, utils.SYSTEM_PATH):
        if path is not None and os.path.exists(path):
            _config.read(path)
            return _config

    conf_file_paths = "\n".join([cwd_path, utils.USER_PATH, utils.SYSTEM_PATH])
    raise exceptions.IRFileNotFoundException(
        conf_file_paths,
        "IR configuration not found. "
        "Please set it in one of the following paths:\n")


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


class SpecManager(object):
    """
    Holds everything related to specs.
    """

    @classmethod
    def parse_args(cls, module_name, config, args=None):
        """
        Looks for all the specs for specified module
        and parses the commandline input arguments accordingly.

        :param module_name: the module name: installer|provisioner|tester
        """

        clg_options, global_opts, subcommand_opts = \
            SpecLoader.load(module_name, config)

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
                    defaults)

        # replace defaults with cli
        utils.dict_merge(res_args, defaults)

        return res_args


class SpecLoader(object):
    """
    Responsible to load spec files.
    """
    SPEC_EXTENSION = '.spec'
    LOOKUP_DICT = {
        '__DEFAULT__': "default"
    }

    TRIM_PARAMS = ['default', 'required']

    @classmethod
    def load(cls, module_name, config):
        """
        Loads the spec file as dict.
        """
        clg_options = cls._get_specs(module_name, config)
        global_options, subcommands_options = cls._get_options(clg_options)
        return clg_options, global_options, subcommands_options

    @classmethod
    def _get_options(cls, spec_dict, lookup=False, trim=False):
        global_options = {}
        subcommand_options = {}
        cls.__get_options(global_options, spec_dict, lookup, trim)
        cls.__get_groups_options(global_options, spec_dict, lookup, trim)
        # collect sub parser global_options
        if 'subparsers' in spec_dict:
            for subparser_name, params in spec_dict['subparsers'].iteritems():
                subcommand_options[subparser_name], _ = cls._get_options(
                    params, lookup=True, trim=True)

        return global_options, subcommand_options

    @classmethod
    def __get_groups_options(cls, options, spec_dict, lookup, trim):
        if 'groups' in spec_dict:
            for group in spec_dict['groups']:
                cls.__get_options(options, group, lookup, trim)

    @classmethod
    def __get_options(cls, options, spec_dict, lookup, trim):
        if 'options' in spec_dict:
            for opt_name, opt_params in spec_dict['options'].iteritems():
                if lookup:
                    cls.lookup_option(opt_name, opt_params)

                # get a parameters copy with all the keys.
                options[opt_name] = dict(opt_params)

                if trim:
                    cls.trim_option(opt_name, opt_params)

    @classmethod
    def lookup_option(cls, opt_name, opt_params):
        # first check __*__ pattern
        for opt_param_name, param_value in opt_params.iteritems():
            for lookup_string, lookup_key in cls.LOOKUP_DICT.iteritems():
                if lookup_string in str(param_value):
                    opt_params[opt_param_name] = \
                        param_value.replace(lookup_string, str(opt_params.get(
                            lookup_key, lookup_string)))

        # insert default value into help.
        if 'help' in opt_params and 'default' in opt_params:
            opt_params['help'] += " | Default value: {}".format(
                opt_params['default'])


    @classmethod
    def trim_option(cls, opt_name, opt_params):
        for opt_param_name, param_value in opt_params.iteritems():
            if opt_param_name in cls.TRIM_PARAMS:
                opt_params.pop(opt_param_name, None)

    @classmethod
    def _get_specs(cls, module_name, config):
        """
        Gets specs files as a dict from settings/<module_name> folder.
        :param module_name: the module name: installer|provisioner|tester
        """
        res = {}
        for spec_file in cls._get_all_specs(config, subfolder=module_name):
            spec = yaml.load(
                open(spec_file),
                Loader=yamlordereddictloader.Loader)
            utils.dict_merge(res, spec)
        return res

    @classmethod
    def _get_all_specs(cls, config, subfolder=None):
        root_dir = utils.validate_settings_dir(
            config.get('defaults', 'settings'))
        if subfolder:
            root_dir = os.path.join(root_dir, subfolder)

        res = []
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in [f for f in filenames
                             if f.endswith(cls.SPEC_EXTENSION)]:
                res.append(os.path.join(dirpath, filename))

        return res


config = load_config_file()

# update clg types
clg.TYPES.update({'IniFile': IniFileType})
