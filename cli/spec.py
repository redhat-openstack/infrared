import ConfigParser
import re
from functools import total_ordering
import sys

import os
import glob
import yaml
import yamlordereddictloader

from cli import exceptions
from cli import logger
from cli import utils
from cli import clg

LOG = logger.LOG

SPEC_EXTENSION = '.spec'


@total_ordering
class ValueArgument(object):
    """
    Default argument type for InfraRed Spec
    Resolves "None" Types with priority defaults.
    """
    settings_dirs = None
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
    def init_missing_args(cls, spec, args, settings_dirs=None,
                          subcommand=None):
        """Initialize defaults for ValueArgument class.

        argparse loads all unprovided arguments as None objects, instead of
        the argument type specified in spec file. This method will set
        argument types according to spec, so later we can iterate of arguments
        by type.

        :param spec: dict. spec file
        :param args: dict. argparse arguments.
        :param settings_dirs: the list of paths to the base directory
            holding the application's settings. App can be
            provisioner\installer\tester
            and the path would be: settings/<app_name>/
        """
        cls.settings_dirs = cls.get_app_attr("settings_dirs") or settings_dirs
        cls.subcommand = cls.get_app_attr("subcommand") or subcommand

        # todo(yfried): consider simply searching for option_name instead of
        # "options"

        # limit spec file with only subparsers spec
        # to avoid name collision when, for example, two specs have the
        # arguments with the same name.
        subcommand_spec = dict(options=spec['options'],
                               subparsers={subcommand:
                                           spec['subparsers'][subcommand]})
        for option_tree in utils.search_tree("options", subcommand_spec):
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
        # override get default from conf file
        if self.value is None:
            self.value = defaults.get(self.arg_name)

    def __eq__(self, other):
        """
        Checks if other value is equal to the current value.
        """
        if isinstance(other, ValueArgument):
            return self.value == other.value
        else:
            return self.value == other

    def __lt__(self, other):
        """
        Checks if current value is less than other value.
        """
        if isinstance(other, ValueArgument):
            return self.value < other.value
        else:
            return self.value < other

    def __repr__(self):
        return self.value


class BaseFileArgument(ValueArgument):
    """
    Base class to load files as a dicts.
    """
    @classmethod
    def get_file_locations(cls, settings_dirs, subcommand, arg_name):
        """
        Get the possible locations (folders) where the
        yaml files can be stored.

        :param settings_dirs: a list of paths to the base directory holding the
            application's settings. App can be provisioner\installer\tester
            and the path would be: settings/<app_name>/
        :param subcommand: the subcommand name (e.g. virsh, ospd, etc)
        :param arg_name: the argument name
        :return The list of folders to search for the yaml files.
        """
        search_locations = [os.path.join(
            settings_path, subcommand, *arg_name.split("-"))
                            for settings_path in settings_dirs]
        root_locations = [os.path.join(
            settings_path, *arg_name.split("-"))
                          for settings_path in settings_dirs]
        search_locations.extend(root_locations)
        search_locations.append(os.getcwd())
        return search_locations


class YamlFileArgument(BaseFileArgument):
    """
    YAML file input argument.
    Loads legal YAML from file.
    Will search for files in the spec settings directories before trying
        to resolve absolute path.

    For the argument name is "arg-name" and of subparser "SUBCOMMAND" of
        application "APP", the default search paths would be:

         settings_dir/APP/SUBCOMMAND/arg/name/arg_value
         settings_dir/APP/arg/name/arg_value
         arg_value

    """

    @classmethod
    def get_allowed_files(cls, settings_dirs, subcommand, arg_name,
                          search_root=False, file_extensions=('yml', 'yaml')):
        """
        Gets the list of the the files in the default locations.

        :param settings_dirs: a list of paths to the base directory holding the
            application's settings. App can be provisioner\installer\tester
            and the path would be: settings/<app_name>/
        :param subcommand: the subcommand name (e.g. virsh, ospd, etc)
        :param arg_name: the argument name
        :param search_root: specify whether the execution root folder
            should be searched for yaml files. By default equals
            to False to avoid unnecessary files.
        :param file_extensions: the list of file extension to look for.
        """

        res = []
        locations = cls.get_file_locations(settings_dirs,
                                           subcommand,
                                           arg_name)
        if search_root is False:
            locations = locations[:-1]
        for folder in locations:
            for ext in file_extensions:
                res.extend(glob.glob(folder + "/*." + ext))

        return res

    def resolve_value(self, arg_name, defaults=None):
        super(YamlFileArgument, self).resolve_value(arg_name, defaults)

        search_paths = self.get_file_locations(
            self.get_app_attr("settings_dirs"),
            self.get_app_attr("subcommand"),
            arg_name)

        if self.value is not None:
            self.value = utils.load_yaml(self.value, *search_paths)
        else:
            pass


class ListOfYamlArgument(BaseFileArgument):
    """
    Builds dicts from smaller YAML files.
    """

    def resolve_value(self, arg_name, defaults=None):
        super(ListOfYamlArgument, self).resolve_value(arg_name, defaults)
        search_paths = self.get_file_locations(
            self.get_app_attr("settings_dirs"),
            self.get_app_attr("subcommand"),
            arg_name)

        if self.value is not None:
            result = {}
            # validate value
            pattern = re.compile("^[-\w\s\.]+(?:,[-\w\s]*)*$")
            if pattern.match(self.value) is None:
                raise exceptions.IRWrongYamlListFormat(self.value)

            for item in self.value.split(','):
                item_name, item_file = self._construct_name(item)
                item_dict = utils.load_yaml(item_file, *search_paths)
                result[item_name] = item_dict

            self.value = result

    @classmethod
    def _construct_name(cls, item, extension=".yml"):
        """
        Gets the name of the file to load.
        """
        if item.endswith(extension):
            result_file = item
            result_name = item[:-len(extension)]
        else:
            result_file = item + extension
            result_name = item
        return result_name, result_file

    @classmethod
    def get_allowed_files(cls, settings_dirs, subcommand, arg_name,
                          search_root=False, file_extensions=('yml', 'yaml')):
        """
        Gets the list of the the files in the default locations.

        :param settings_dirs: a list of paths to the base directory holding the
            application's settings. App can be provisioner\installer\tester
            and the path would be: settings/<app_name>/
        :param subcommand: the subcommand name (e.g. virsh, ospd, etc)
        :param arg_name: the argument name
        :param search_root: specify whether the execution root folder
            should be searched for yaml files. By default equals
            to False to avoid unnecessary files.
        :param file_extensions: the list of file extension to look for.
        """

        res = []
        locations = cls.get_file_locations(settings_dirs,
                                           subcommand,
                                           arg_name)
        if search_root is False:
            locations = locations[:-1]
        for folder in locations:
            for ext in file_extensions:
                res.extend(os.path.splitext(os.path.basename(file_name))[0]
                           for file_name in glob.glob(folder + "/*." + ext))

        return res


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
        topology_dirs = [os.path.join(path,
                                      'topology') for path in
                         self.get_app_attr("settings_dirs")]
        topology_dict = {}
        for topology_item in self.value.split(','):

            node_type, number = None, None

            pattern = re.compile("^[A-Za-z]+:[0-9]+$")
            if pattern.match(topology_item) is None:
                pattern = re.compile("^[0-9]+_[A-Za-z]+$")
                if pattern.match(topology_item) is None:
                    raise exceptions.IRWrongTopologyFormat(self.value)
                number, node_type = topology_item.split('_')
                LOG.warning("This topology format is deprecated and will be "
                            "removed in future versions. Please see `--help` "
                            "for proper format")
            else:
                node_type, number = topology_item.split(':')

            # Remove white spaces
            node_type = node_type.strip()

            # todo(obaraov): consider moving topology to config on constant.
            topology_dict[node_type] = utils.load_yaml(node_type + ".yml",
                                                       *topology_dirs)
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


class ArgumentsPreProcessor(object):
    """
    The helper class which is responsible to to transform input cli arguments
    prior passing them to the clg module for parsing.

    This class will do the following:
     * remove required and default arguments, because cli arguments can be
        overridden by environment and file variables
     * add default values to the help message
     * add the available yaml files for the yaml options to the help
     * replace __*__ patterns in option attributes (
        see https://clg.readthedocs.org/en/latest/configuration.html#options)

    Example:
        Original arguments dict:

        options:
            opt1:
                type: YamlValue
                help: Simple test value
                required: yes

        Resulting arguments dict:

        options:
            opt1:
                type: YamlValue
                help: |
                    Simple test value.
                    Default value: 'myvalue'
                    Available files: { file1.yml, file2.yml }

    """
    BUILTINS_REPLACEMENT = {
        '__DEFAULT__': "default"
    }

    TRIM_PARAMS = ['default', 'required']

    def __init__(self, settings_dirs, app_settings_dirs):
        self.app_settings_dirs = app_settings_dirs
        self.settings_dirs = settings_dirs

    def process(self, spec_dict):
        """
        Goes through all the spec options and modifies them by removing some
        options parameters (like defaults) and adding additional help info.

        :param spec_dict: the dictionary with key obtained from spec files
        :return the list of
        """
        # Collect sub parsers options
        options = {}
        for sub_parser, params in spec_dict.get('subparsers', {}).iteritems():
            parser_options = self._process_options(params, sub_parser)

            # go over the groups if present
            group_options = {}
            for group in params.get('groups', {}):
                group_options.update(self._process_options(group, sub_parser))

            utils.dict_merge(parser_options, group_options)
            options[sub_parser] = parser_options

        return options

    def _process_options(self, spec_dict, subcommand):
        """
        Gets the dict of options listed in the spec of group.

        This method will also remove some methods and will replace
         __<value>__ pattens in the option properties
         (e.g. __default__, __FILE__)

        :param spec_dict: the dictionary to look for new options.
        :param sub_parser: the subcommand name.
        """
        options_dict = {}
        # TODO(aopincar): The 'help' check should be removed  when CLG refactor
        #  is  merged
        help_given = False
        if any([_help in sys.argv for _help in ('--help', '-h')]):
            help_given = True

        for option, attributes in spec_dict.get('options', {}).iteritems():
            self._add_default_to_option_help(attributes)
            self._add_yaml_info(option, attributes, subcommand)

            if not help_given:
                self._replace_builtin(attributes)

            # Get a parameters copy with all the keys.
            options_dict[option] = dict(attributes)

            if not help_given:
                self._trim_option(attributes)

        return options_dict

    def _add_yaml_info(self, option_name, option_attributes, subcommand):
        """
        Adds the list of available yaml files to the help message.
        :param option_name: the option name (key)
        :param option_attributes: dictionary with option attributes (help,
        type, default, etc)
        :param subcommand: the subcommand name
        """
        allowed_values = _get_option_allowed_values(
            self.app_settings_dirs,
            subcommand,
            option_name,
            option_attributes)

        if allowed_values:
            option_attributes['help'] += "\nAllowed values: {{ {0} }}".format(
                ", ".join(map(os.path.basename, allowed_values))
            )

    def _add_default_to_option_help(self, option_attributes):
        """
        Update the help by inserting default values if required.

        :param option_attributes: dictionary with option attributes (help,
        type, default, etc)
        """
        # Insert default value into help.
        if all(attr in option_attributes for attr in ('help', 'default')) \
                and '__DEFAULT__' not in option_attributes['help']:
            option_attributes['help'] += "\nDefault value: {}".format(
                option_attributes['default'])

    def _replace_builtin(self, option_attributes):
        """
        Modifies existing option parameters by replacing __*__ patterns

        :param option_attributes: dictionary with option attributes (help,
        type, default, etc)
        """
        # check __*__ pattern
        for attr_key, attr_value in option_attributes.iteritems():
            for builtin, replacement in self.BUILTINS_REPLACEMENT.iteritems():
                if builtin in str(attr_value):
                    option_attributes[attr_key] = \
                        attr_value.replace(builtin, str(
                            option_attributes.get(replacement, builtin)))

    def _trim_option(self, option_attributes):
        """
        Removes the defined option parameters.

        :param option_attributes: dictionary with option attributes (help,
        type, default, etc)
        """
        for trim_param in self.TRIM_PARAMS:
            option_attributes.pop(trim_param, None)


def parse_args(settings_dirs, app_settings_dirs, args=None):
    """
    Looks for all the specs for specified app
    and parses the commandline input arguments accordingly.

    Trim clg spec from customized input and modify help data.

    :param settings_dirs: a list of paths to the settings folders
    :param app_settings_dirs: the list of pathes to the base directory holding
        the application's settings. App can be provisioner\installer\tester
        and the path would be: settings/<app_name>/
    :param args: the list of arguments used for directing the method to work
        on something other than CLI input (for example, in testing).
    :return: dict. Based on cmd-line args parsed from spec file
    """
    # Dict with the merging result of all app's specs
    common_specs = _get_specs(settings_dirs, include_subfolders=False)
    app_specs = _get_specs(app_settings_dirs)
    utils.dict_merge(app_specs, common_specs)

    # Get the subparsers options as is with all the fields from app's specs.
    # This also trims some custom fields from options to pass to clg if the
    # help option wasn't given
    subparsers_options = ArgumentsPreProcessor(
        settings_dirs, app_settings_dirs).process(app_specs)

    # Pass trimmed spec to clg with modified help message
    cmd = clg.CommandLine(app_specs)
    clg_args = vars(cmd.parse(args))
    ValueArgument.init_missing_args(app_specs, clg_args, app_settings_dirs,
                                    subcommand=clg_args["command0"])

    # Current sub-parser options
    sub_parser_options = subparsers_options.get(clg_args['command0'], {})

    override_default_values(app_settings_dirs, clg_args, sub_parser_options)
    return clg_args


def override_default_values(app_settings_dirs, clg_args, sub_parser_options):
    """
    Collects arguments values from the different sources and resolve values.

    Each argument value is resolved in the following priority:
    1. Explicitly provided from cmd-line
    2. Environment variable
    3. Provided configuration file.
    4. Spec defaults

    :param app_settings_dirs: the application settings dir.
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
            app_settings_dirs=app_settings_dirs,
            subcommand=clg_args['command0'],
            defaults=defaults,
            all_options=sub_parser_options)
    else:
        # Override defaults with the ini file args if provided
        file_args = getattr(clg_args.get('from-file'), "value", {}).get(
            clg_args['command0'], {})
        utils.dict_merge(defaults, file_args)

        # Override defaults with env values
        # TODO (aopincar): IR env vars should be more uniques
        env_vars = {}
        for arg_name, arg_obj in clg_args.iteritems():
            arg_value = os.getenv(arg_name.upper().replace("-", "_"))
            if arg_value:
                env_vars[arg_name] = arg_value
        utils.dict_merge(defaults, env_vars)

        # Resolve defaults and load values to clg_args
        non_cli_args = []
        for arg_name, arg_obj in clg_args.iteritems():
            if isinstance(arg_obj, ValueArgument):
                # check what values were not provided in cli
                if arg_obj.value is None:
                    non_cli_args.append(arg_name)
                arg_obj.resolve_value(arg_name, defaults)

        # Now when we have all the values check what default values we have
        # and show warning to inform user that we took something from
        # defaults
        default_args = set(non_cli_args).difference(
            file_args.keys()).difference(env_vars.keys())

        for arg_name in default_args:
            if arg_name in defaults:
                LOG.warning(
                    "Argument '{}' was not supplied. "
                    "Using: '{}' as default.".format(
                        arg_name, defaults[arg_name]))

        _check_required_arguments(clg_args, sub_parser_options)


def _check_required_arguments(clg_args, sub_parser_options):
    """
    Verify all the required arguments are set.

    :param clg_args: Dictionary based on cmd-line args parsed by clg
    :param sub_parser_options: Dictionary with all the options attributes for
        a sub-command.
    """
    unset_args = []
    for option, attributes in sub_parser_options.iteritems():
        if attributes.get('required'):
            # safely get the attribute provided value
            value = clg_args.get(option, None)
            if hasattr(value, 'value'):
                value = value.value
            if value is None:
                unset_args.append(option)
    if unset_args:
        raise exceptions.IRConfigurationException(
            "Required input arguments {} are not set!".format(unset_args))


def _generate_config_file(
        file_name, app_settings_dirs, subcommand, defaults, all_options):
    """
    Generates configuration file based on defaults from specs

    :param file_name: Name of the new configuration that will be generated.
    :param subcommand: The subparser for which the conf file is generated
    :param defaults: the default options values.
    :param all_options: The dict with all the possible spec options
    """
    out_config = ConfigParser.ConfigParser(allow_no_value=True)
    out_config_old = ConfigParser.ConfigParser(allow_no_value=True)

    # reuse existing file
    if os.path.exists(file_name):
        out_config_old.read(file_name)

    # todo(obaranov) we lose help from other sections
    for old_section in out_config_old.sections():
        if old_section != subcommand:
            out_config.add_section(old_section)
            for option in out_config_old.options(old_section):
                out_config.set(old_section, option,
                               out_config_old.get(old_section, option))
    # put defaults values
    if not out_config.has_section(subcommand):
        out_config.add_section(subcommand)

    for opt, value in defaults.iteritems():
        if out_config_old.has_option(subcommand, opt):
            value = out_config_old.get(subcommand, opt)
        _add_help_comment(out_config, subcommand, all_options.get(opt, {}))
        out_config.set(subcommand, opt, value)

    # add required options
    for opt, attributes in all_options.iteritems():
        if attributes.get('required') \
                and not out_config.has_option(subcommand, opt):
            if not out_config_old.has_option(subcommand, opt):
                # get available value:
                allowed_values = _get_option_allowed_values(app_settings_dirs,
                                                            subcommand, opt,
                                                            attributes)

                if allowed_values:
                    message = "one of {} options".format(allowed_values)
                else:
                    message = "any value"
                LOG.warning(
                    "Required argument '{0}' not supplied. "
                    "Please edit config file with {1}, OR override "
                    "through CLI: --{0}=<option>. "
                    "".format(opt, message))

                # add comment
                _add_help_comment(out_config, subcommand, attributes)
                out_config.set(
                    subcommand,
                    opt,
                    "Edit with {0}, "
                    "OR override with CLI: --{1}=<option>".format(
                        message, opt))
            else:
                # add existing value.
                _add_help_comment(out_config, subcommand, attributes)
                out_config.set(
                    subcommand,
                    opt,
                    out_config_old.get(subcommand, opt))

    with open(file_name, 'w') as configfile:  # save
        out_config.write(configfile)


def _add_help_comment(config_parser, section, option_attributes):
    """
    Gets the short help message for an option.
    """

    if option_attributes.get('help', None):
        for sub_help in option_attributes.get('help').split('\n'):
            config_parser.set(section, "# " + sub_help)


def _get_option_allowed_values(app_settings_dirs, subcommand, option,
                               attributes):
    """
    Gets the list of allowed values for an option.
    """
    if attributes.get('type', None) in ['YamlFile', 'ListOfYamls']:
        allowed_values = map(
            os.path.basename, clg.TYPES[attributes['type']].get_allowed_files(
                app_settings_dirs, subcommand, option))
    else:
        allowed_values = attributes.get('choices', [])
    return allowed_values


def _get_specs(app_settings_dirs, include_subfolders=True):
    """
    Load all  specs files from base settings directory.

    :param app_settings_dirs: the list of paths to the base directory holding
        the application's settings. App can be provisioner\installer\tester
        and the path would be: settings/<app_name>/
    :param include_subfolders: specifies whether the subfolders of the root
        folder should be also searched for a spec files.
    :return: dict: All spec files merged into a single dict.
    """

    # Collect all app's spec
    spec_files = []
    if include_subfolders:
        for app_settings_dir in app_settings_dirs:
            for root, _, files in os.walk(app_settings_dir):
                spec_files.extend(
                    [os.path.join(root, a_file) for a_file in files
                     if a_file.endswith(SPEC_EXTENSION)])
    else:
        spec_files = []
        for app_settings_dir in app_settings_dirs:
            spec_files.extend(glob.glob(
                './' + app_settings_dir + '/*' + SPEC_EXTENSION))

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
clg.TYPES.update({'ListOfYamls': ListOfYamlArgument})
