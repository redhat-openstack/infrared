import ConfigParser

import clg
import os
import yaml
import yamlordereddictloader

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
    settings_dir = None
    subcommand = None

    def __init__(self, value=None, required=None):
        self.value = value
        self.arg_name = None
        self.required = None

    @classmethod
    def get_app_attr(cls, attribute):
        """Get class attributes from ancestor tree.

        If attribute isn't initialized, search ancestor tree for it and
        initialize attribute with the first match found.

        :param attribute: class attribute.
        :return:
        """
        if getattr(cls, attribute):
            return getattr(cls, attribute)
        try:
            setattr(cls, attribute,
                    super(ValueArgument, cls).get_app_attr(attribute))
        except AttributeError:
            pass
        return getattr(cls, attribute)

    @classmethod
    def init_missing_args(cls, spec, args, settings_dir=None, subcommand=None):
        """Initialize defaults for ValueArgument class.

        argparse loads all unprovided arguments as None objects, instead of
        the argument type specified in spec file. This method will set
        argument types according to spec, so later we can iterate of arguments
        by type.

        :param spec: dict. spec file
        :param args: dict. argparse arguments.
        :param app_settings_dir: path to the base directory holding the
            application's settings. App can be provisioner\installer\tester
            and the path would be: settings/<app_name>/
        """
        cls.settings_dir = cls.get_app_attr("settings_dir") or settings_dir
        cls.subcommand = cls.get_app_attr("subcommand") or subcommand

        # todo(yfried): consider simply searching for option_name instead of
        # "options"
        for option_tree in utils.search_tree("options", spec):
            for option_name, option_dict in option_tree.iteritems():
                if option_name in args and issubclass(
                        clg.TYPES.get(option_dict.get(
                            "type", object),
                            object),
                        cls) and args[option_name] is None:
                    args[option_name] = clg.TYPES.get(option_dict["type"])(
                        required=option_dict.get("required")
                    )
                    # todo(yfried): this is a good place to trigger
                    # args[option_name].resolve_value()

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
        # TODO (aopincar): IR env vars should be more uniques
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

    For the argument name is "arg-name" and of subparser "SUBCOMMAND" of
        application "APP", the default search path would be:

         settings_dir/APP/SUBCOMMAND/arg/name/arg_value
    """

    def resolve_value(self, arg_name, defaults=None):
        super(YamlFileArgument, self).resolve_value(arg_name, defaults)
        search_first = os.path.join(self.get_app_attr("settings_dir"),
                                    self.get_app_attr("subcommand"),
                                    *arg_name.split("-"))
        self.value = utils.load_yaml(self.value, search_first)


class TopologyArgument(ValueArgument):
    """Build topology dict from smaller YAML files by parsing input. """

    def resolve_value(self, arg_name, defaults=None):
        """
        Merges topology files in a single topology dict.

        :param clg_args: Dictionary based on cmd-line args parsed by clg
        :param app_settings_dir: path to the base directory holding the
            application's settings. App can be provisioner\installer\tester
            and the path would be: settings/<app_name>/
        """
        super(TopologyArgument, self).resolve_value(arg_name, defaults)

        # post process topology
        topology_dir = os.path.join(self.get_app_attr("settings_dir"),
                                    'topology')
        topology_dict = {}
        for topology_item in self.value.split(','):
            if '_' in topology_item:
                number, node_type = topology_item.split('_')
            else:
                raise exceptions.IRConfigurationException(
                    "Topology node should be in format  <number>_<node role>. "
                    "Current value: '{}' ".format(topology_item))
            # todo(obaraov): consider moving topology to config on constant.
            topology_dict[node_type] = utils.load_yaml(node_type + ".yaml",
                                                       topology_dir)
            topology_dict[node_type]['amount'] = int(number)

        self.value = topology_dict


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
    :return: dict. Based on cmd-line args parsed from spec file
    """
    # Dict with the merging result of all app's specs
    app_specs = _get_specs(app_settings_dir)

    # Get the subparsers options as is with all the fields from app's specs.
    # This also trims some custom fields from options to pass to clg.
    subparsers_options = _get_subparsers_options(app_specs)

    # Pass trimmed spec to clg with modified help message
    cmd = clg.CommandLine(app_specs)
    clg_args = vars(cmd.parse(args))
    ValueArgument.init_missing_args(app_specs, clg_args, app_settings_dir,
                                    subcommand=clg_args["command0"])

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
    # todo(yfried): move to init_missing_args
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
        # Override defaults with the ini file args if provided
        file_args = getattr(clg_args.get('from-file'), "value", {}).get(
            clg_args['command0'], {})
        utils.dict_merge(defaults, file_args)

        # Resolve defaults and load values to clg_args
        for arg_name, arg_obj in clg_args.iteritems():
            if isinstance(arg_obj, ValueArgument):
                arg_obj.resolve_value(arg_name, defaults)

        _check_required_arguments(clg_args)


def _check_required_arguments(clg_args):
    """
    Verify all the required arguments are set.

    :param clg_args: Dictionary based on cmd-line args parsed by clg
    """
    # Only missing args initialize "required" attr in init_missing_args
    unset_args = [arg.arg_name for arg in clg_args.values() if
                  getattr(arg, 'required', False)]

    # todo(yfried): revisit this in the future
    # only_args = []
    # for arg in clg_args.values():
    #     if 'requires_only' in attributes:
    #         only_args.extend(attributes['requires_only'])

    # if only_args:
    #     intersection = set(unset_args).intersection(set(only_args))
    #     if intersection:
    #         raise exceptions.IRConfigurationException(
    #             "Missing mandatory arguments: {}".format(
    #                 list(intersection)))
    if unset_args:
        raise exceptions.IRConfigurationException(
            "Required input arguments {} are not set!".format(unset_args))


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
clg.TYPES.update({'Topology': TopologyArgument})
clg.TYPES.update({'YamlFile': YamlFileArgument})
