import ConfigParser

import clg
import os
import yaml
import yamlordereddictloader
from cli import exceptions
from cli import utils
from cli import logger

LOG = logger.LOG
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


# todo(yfried) move to spec.py
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


class IniFileType(object):
    """Create dict from conf files

    :param value: path to file.
    :return: dict based on a provided ini file.
    """

    def __init__(self, value):
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

        self.value = d


class SpecManager(object):
    """
    Holds everything related to specs.
    """

    SPEC_EXTENSION = '.spec'

    @classmethod
    def parse_args(cls, module_name, config, args=None):
        """
        Looks for all the specs for specified module
        and parses the commandline input arguments accordingly.

        :param module_name: the module name: installer|provisioner|tester
        """
        clg_spec = cls._get_specs(module_name, config)
        cmd = clg.CommandLine(clg_spec)
        res_args = vars(cmd.parse(args))
        cls._load_defaults(clg_spec, res_args)

        # always load default values for command0
        default_file = os.path.join(
            config.get('defaults', 'settings'),
            module_name,
            res_args['command0'],
            DEFAULT_INI
        )
        defaults = IniFileType(default_file).value[res_args['command0']]

        # override defaults with the ini file args
        if 'from-file' in res_args:
            file_args = res_args['from-file'].value
            if file_args is not None and res_args['command0'] in file_args:
                defaults = utils.dict_merge(
                    file_args[res_args['command0']],
                    defaults)

        # Resolve defaults and load values to res_args
        for arg_name, arg_obj in res_args.iteritems():
            if isinstance(arg_obj, ValueArgument):
                arg_obj.resolve_value(arg_name, defaults)
                # res_args[arg_name] = arg_obj.value

        return res_args

    @classmethod
    def _load_defaults(cls, spec, args):
        """Initialize defaults for ValueArgument class.

        argparse loads all unprovided arguments as None objects, instead of
        the argument type specified in spec file. This method will set
        argument types according to spec, so later we can iterate of arguments
        by type.

        :param spec: dict. spec file
        :param args: dict. argparse arguments.
        """
        # todo(yfried): cosider simply searching for option_name instead of
        # "options"
        for option_tree in utils.search_tree(spec, "options"):
            for option_name, option_dict in option_tree.iteritems():
                if issubclass(clg.TYPES.get(option_dict.get("type", object),
                                            object),
                              ValueArgument) and args[option_name] is None:
                    args[option_name] = clg.TYPES.get(option_dict["type"])()
                    # todo(yfried): this is a good place to trigger
                    # args[option_name].resolve_value()

    @classmethod
    def _get_specs(cls, module_name, config):
        """
        Gets specs files as a dict from settings/<module_name> folder.
        :param module_name: the module name: installer|provisioner|tester
        """
        res = {}
        for spec_file in cls._get_all_specs(config, subfolder=module_name):
            spec = yaml.load(open(spec_file),
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
clg.TYPES.update({'Value': ValueArgument})
clg.TYPES.update({'YamlFile': YamlFileArgument})
