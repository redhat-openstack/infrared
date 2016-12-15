from ConfigParser import ConfigParser
from collections import OrderedDict
import os

# TODO(aopincar): Add pip to the project's requirements
import pip

from infrared.core.utils import logger


LOG = logger.LOG
DEFAULT_PLUGIN_INI = dict(
    supported_types=dict(
        provision='Provisioning plugins',
        install='Installing plugins',
        test='Testing plugins'
    )
)


# TODO(aopincar): add use in abspath everywhere file paths are in use


# TODO(aopincar): replace this Singleton class with anonymous class
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = \
                super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class InfraRedPluginManager(object):
    __metaclass__ = Singleton

    PLUGINS_DICT = OrderedDict()
    SUPPORTED_TYPES_SECTION = 'supported_types'

    def __init__(self, plugins_conf=None):
        """
        :param plugins_conf: A path to the main plugins configuration file
        """
        self.config = plugins_conf
        self._load_plugins()

    def _load_plugins(self):
        for plugin_type_section in self.config.options(
                self.SUPPORTED_TYPES_SECTION):
            self.__class__.PLUGINS_DICT[plugin_type_section] = {}
            if self.config.has_section(plugin_type_section):
                for plugin_name, plugin_path in self.config.items(
                        plugin_type_section):
                    plugin = InfraRedPlugin(plugin_path)
                    self.__class__.PLUGINS_DICT[
                        plugin_type_section][plugin_name] = plugin

    @property
    def config_file(self):
        return self._config_file

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, plugins_conf):

        if plugins_conf is None:
            from infrared.core.services import CoreServices
            plugins_conf = os.path.join(
                os.path.dirname(CoreServices.INFRARED_CONF),
                CoreServices.DEFAULTS['plugins_conf_file']
            )
            LOG.warning("Plugin conf file hasn't been given, trying to load "
                        "it from the default path: '{}'".format(plugins_conf))

        plugins_conf_full_path = \
            os.path.abspath(os.path.expanduser(plugins_conf))

        if not os.path.isfile(plugins_conf_full_path):
            LOG.warning("Plugin conf ('{}') not found, creating it with "
                        "default data".format(plugins_conf_full_path))
            with open(plugins_conf_full_path, 'w') as fp:
                config = ConfigParser()

                for section, section_data in DEFAULT_PLUGIN_INI.items():
                    if not config.has_section(section):
                        config.add_section(section)
                    for option, value in section_data.items():
                        config.set(section, option, value)

                config.write(fp)

        self._config_file = plugins_conf_full_path

        with open(plugins_conf_full_path) as fp:
            self._config = ConfigParser()
            self.config.readfp(fp)

    def get_desc_of_type(self, s_type):
        """ Return the description of the given supported plugin type

        :param s_type: The type of the plugin you want the description
        :return: String of the supported plugin description
        """
        return self.config.get(self.SUPPORTED_TYPES_SECTION, s_type)

    @classmethod
    def get_plugin(cls, plugin_type, plugin_name):
        """Returns an instance of plugin based on the given type & name

        :param plugin_type: Plugin type
        :param plugin_name: Plugin name
        :return: InfraRedPlugin instance
        """
        for plugin in cls.PLUGINS_DICT[plugin_type]:
            if plugin.name == plugin_name:
                return plugin

    def __iter__(self):
        for plugin in self.PLUGINS_DICT.iteritems():
            yield plugin
        else:
            raise StopIteration

    def add_plugin(self, plugin_path):
        plugin = InfraRedPlugin(plugin_path)
        plugin_type = plugin.config['plugin_type']
        # FIXME(yfried) validate spec and throw exception on missing input

        if plugin_type not in self.config.options(
                self.SUPPORTED_TYPES_SECTION):
            # TODO(aopincar): Replace with a proper InfraRed exception
            raise Exception(
                "Unsupported plugin type: '{}'".format(plugin_type))

        if not self.config.has_section(plugin_type):
            self.config.add_section(plugin_type)

        self.config.set(plugin_type, plugin.name, plugin.path)

        with open(self.config_file, 'w') as fp:
            self.config.write(fp)

        self._install_requirements(plugin_path)
        self._load_plugins()

    def remove_plugin(self, plugin_type, plugin_name):
        if plugin_type not in self.config.options(
                self.SUPPORTED_TYPES_SECTION):
            # TODO(aopincar): Replace with a proper InfraRed exception
            LOG.error(
                "Unsupported plugin type: '{}'".format(plugin_type))
        elif not self.config.has_section(plugin_type):
            LOG.error(
                "There are no plugins of type '{}' installed".format(
                    plugin_type))
        elif not self.config.has_option(plugin_type, plugin_name):
            LOG.error(
                "Plugin named '{}' of type '{}' isn't installed".format(
                    plugin_name, plugin_type))
        else:
            self.config.remove_option(plugin_type, plugin_name)
            if not self.config.options(plugin_type):
                self.config.remove_section(plugin_type)
            with open(self.config_file, 'w') as fp:
                self.config.write(fp)
            self._load_plugins()

    @property
    def supported_plugin_types(self):
        return self.config.options(self.SUPPORTED_TYPES_SECTION)

    @staticmethod
    def _install_requirements(plugin_path):
        requirement_file = os.path.join(plugin_path, "plugin_requirements.txt")
        if os.path.isfile(requirement_file):
            LOG.info(
                "Installing requirements from: {}".format(requirement_file))
            pip_args = ['install', '-r', requirement_file]
            pip.main(args=pip_args)


class InfraRedPlugin(object):
    PLUGIN_SPEC_FILE = 'plugin.spec'

    # PLUGIN_DIRS = dict(
    #     settings='settings',
    #     modules='library',
    #     roles='roles',
    #     playbooks='playbooks'
    # )

    def __init__(self, plugin_dir):
        """

        :param plugin_path: A path to the plugin's root dir
        """
        self.path = plugin_dir
        self.config = os.path.join(self.path, self.PLUGIN_SPEC_FILE)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, plugin_dir):
        full_path = os.path.abspath(os.path.expanduser(plugin_dir))
        if not os.path.isdir(full_path):
            # TODO(aopincar): Replace with a proper InfraRed exception
            raise IOError(
                "Path to plugin dir '{}' doesn't exist".format(plugin_dir))
        self._path = full_path

    @property
    def spec(self):
        if not getattr(self, '_spec', None):
            self._spec = os.path.join(self.path, self.PLUGIN_SPEC_FILE)
        return self._spec

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, plugin_spec):
        if not os.path.isfile(plugin_spec):
            # TODO(aopincar): Replace with a proper InfraRed exception
            raise IOError(
                "Plugin config '{}' doesn't exist".format(plugin_spec))
        import yaml
        with open(plugin_spec) as fp:
            self._config = yaml.load(fp)

    @property
    def name(self):
        subparsers = self.config['subparsers']
        plugins = subparsers.keys()
        if len(plugins) != 1:
            # TODO(aopincar): Replace with a proper InfraRed exception
            raise Exception("Only one plugin should be defined in spec")
        return plugins[0]

    @property
    def description(self):
        return self.config['description']

    @property
    def help(self):
        subparsers = self.config['subparsers']
        return subparsers[self.name]['help']

    def __repr__(self):
        return self.name

    @property
    def settings_file(self, ext='.yml'):
        """Returns the main plugin's settings file. """

        settings_file = os.path.join(self.path, self.name + ext)
        if not os.path.isfile(settings_file):
            # TODO(aopincar): Replace with a proper InfraRed exception
            raise IOError("Settings file for plugin {} not found")

        return settings_file
