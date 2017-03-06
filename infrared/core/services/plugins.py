from ConfigParser import ConfigParser
from collections import OrderedDict
import glob
import os
import shutil
import subprocess
import tempfile

# TODO(aopincar): Add pip to the project's requirements
import pip

from infrared.core.utils import logger
from infrared.core.utils.exceptions import IRFailedToAddPlugin
from infrared.core.utils.exceptions import IRFailedToRemovePlugin

DEFAULT_PLUGIN_INI = dict(
    supported_types=OrderedDict([
        ('provision', 'Provisioning plugins'),
        ('install', 'Installing plugins'),
        ('test', 'Testing plugins'),
        ('other', 'Other type plugins'),
    ])
)

PLUGINS_REGISTRY = {
    'beaker': 'plugins/beaker',
    'collect-logs': 'plugins/collect-logs',
    'foreman': 'plugins/foreman',
    'openstack': 'plugins/openstack',
    'packstack': 'plugins/packstack',
    'rally': 'plugins/rally',
    'tempest': 'plugins/tempest',
    'tripleo-overcloud': 'plugins/tripleo-overcloud',
    'tripleo-undercloud': 'plugins/tripleo-undercloud',
    'virsh': 'plugins/virsh',
    'gabbi': 'plugins/gabbi'
}

MAIN_PLAYBOOK = "main.yml"
PLUGINS_DIR = os.path.abspath("./plugins")
LOG = logger.LOG


class InfraredPluginManager(object):

    PLUGINS_DICT = OrderedDict()
    SUPPORTED_TYPES_SECTION = 'supported_types'

    def __init__(self, plugins_conf=None):
        """
        :param plugins_conf: A path to the main plugins configuration file
        """
        self.config = plugins_conf
        self._load_plugins()

    def _load_plugins(self):
        self.__class__.PLUGINS_DICT.clear()
        for plugin_type_section in self.config.options(
                self.SUPPORTED_TYPES_SECTION):
            if self.config.has_section(plugin_type_section):
                for plugin_name, plugin_path in self.config.items(
                        plugin_type_section):
                    plugin = InfraredPlugin(plugin_path)
                    self.__class__.PLUGINS_DICT[plugin_name] = plugin

    @staticmethod
    def get_installed_plugins():
        """Returns a dict with project's plugins categorized by type"""
        plugins_dict = {}

        for plugin_dir in glob.glob(PLUGINS_DIR + '/*/'):
            plugin = InfraredPlugin(plugin_dir)
            if plugin.type not in plugins_dict:
                plugins_dict[plugin.type] = [plugin.name]
            else:
                plugins_dict[plugin.type].append(plugin.name)

        return plugins_dict

    def get_all_plugins(self):
        """Returns a dict with all plugins (installed & available)

        The plugins categorized by type and each plugin name contains a boolean
        value which tells if the plugin installed or not
        """
        all_plugins_dict = OrderedDict((plugin_type, {}) for plugin_type
                                       in self.supported_plugin_types)
        for installed_plugin_name in self.PLUGINS_DICT:
            plugin = self.get_plugin(installed_plugin_name)
            if plugin.type not in all_plugins_dict:
                all_plugins_dict[plugin.type] = {plugin.name: True}
            else:
                all_plugins_dict[plugin.type][plugin.name] = True

        for plugins_type, plugins in self.get_installed_plugins().iteritems():
            for plugin_name in plugins:
                if plugin_name in self.PLUGINS_DICT:
                    continue

                if plugins_type not in all_plugins_dict:
                    all_plugins_dict[plugins_type] = {plugin_name: False}
                else:
                    all_plugins_dict[plugins_type][plugin_name] = False

        return all_plugins_dict

    @property
    def config_file(self):
        return self._config_file

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, plugins_conf):
        plugins_conf_full_path = \
            os.path.abspath(os.path.expanduser(plugins_conf))

        init_plugins_conf = False
        if not os.path.isfile(plugins_conf_full_path):
            LOG.warning("Plugin conf ('{}') not found, creating it with "
                        "default data".format(plugins_conf_full_path))
            init_plugins_conf = True
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

        # TODO(aopincar): Remove auto plugins installation when conf is missing
        if init_plugins_conf:
            self.add_all_available()

    def get_desc_of_type(self, s_type):
        """Returns the description of the given supported plugin type

        :param s_type: The type of the plugin you want the description
        :return: String of the supported plugin description
        """
        return self.config.get(self.SUPPORTED_TYPES_SECTION, s_type)

    @classmethod
    def get_plugin(cls, plugin_name):
        """Returns an instance of plugin based on name

        :param plugin_name: Plugin name
        :return: InfraredPlugin instance
        """
        return cls.PLUGINS_DICT[plugin_name]

    def __iter__(self):
        for plugin in self.PLUGINS_DICT.iteritems():
            yield plugin
        else:
            raise StopIteration

    @staticmethod
    def _clone_git_plugin(git_url, dest_dir=None):
        """Clone a plugin into a given destination directory

        :param git_url: Plugin's Git URL
        :param dest_dir: destination where to clone a plugin into (if 'source'
          is a Git URL)
        :return: Path to plugin cloned directory (str)
        """
        dest_dir = os.path.abspath(dest_dir or "plugins")

        tmpdir = tempfile.mkdtemp(prefix="ir-")
        cwd = os.getcwdu()
        os.chdir(tmpdir)
        try:
            subprocess.check_output(["git", "clone", git_url])
        except subprocess.CalledProcessError:
            shutil.rmtree(tmpdir)
            raise IRFailedToAddPlugin(
                "Cloning git repo {} is failed".format(git_url))
        cloned = os.listdir(tmpdir)
        plugin_dir_name = cloned[0]

        plugin_source = os.path.join(dest_dir, plugin_dir_name)
        shutil.copytree(os.path.join(tmpdir, plugin_dir_name),
                        plugin_source)
        os.chdir(cwd)
        shutil.rmtree(tmpdir)

        return plugin_source

    def add_plugin(self, plugin_source, dest=None):
        """Adds (install) a plugin

        :param plugin_source: Plugin source.
          Can be:
            1. Plugin name (from available in registry)
            2. Path to a local directory
            3. Git URL
        :param dest: destination where to clone a plugin into (if 'source' is
          a Git URL)
        """
        # Check if a plugin is in the registry
        if plugin_source in PLUGINS_REGISTRY:
            plugin_source = PLUGINS_REGISTRY[plugin_source]

        # Local dir plugin
        if os.path.exists(plugin_source):
            pass
        # Git Plugin
        else:
            plugin_source = self._clone_git_plugin(plugin_source, dest)

        plugin = InfraredPlugin(plugin_source)
        plugin_type = plugin.config['plugin_type']
        # FIXME(yfried) validate spec and throw exception on missing input

        if plugin_type not in self.config.options(
                self.SUPPORTED_TYPES_SECTION):
            raise IRFailedToAddPlugin(
                "Unsupported plugin type: '{}'".format(plugin_type))

        if not self.config.has_section(plugin_type):
            self.config.add_section(plugin_type)
        elif self.config.has_option(plugin_type, plugin.name):
            raise IRFailedToAddPlugin(
                "Plugin with the same name & type already exists")

        self.config.set(plugin_type, plugin.name, plugin.path)

        with open(self.config_file, 'w') as fp:
            self.config.write(fp)

        self._install_requirements(plugin_source)
        self._load_plugins()

    def add_all_available(self):
        """Add all available plugins which aren't already installed"""
        for plugin in set(PLUGINS_REGISTRY) - \
                set(self.PLUGINS_DICT):
            self.add_plugin(plugin)
            LOG.warning(
                "Plugin '{}' has been successfully installed".format(plugin))

    def remove_plugin(self, plugin_name):
        """Removes an installed plugin

        :param plugin_name: Plugin name to be removed
        """
        if plugin_name not in self.PLUGINS_DICT:
            raise IRFailedToRemovePlugin(
                "Plugin '{}' isn't installed and can't be removed".format(
                    plugin_name))

        plugin = InfraredPluginManager.get_plugin(plugin_name)

        self.config.remove_option(plugin.type, plugin_name)
        if not self.config.options(plugin.type):
            self.config.remove_section(plugin.type)
        with open(self.config_file, 'w') as fp:
            self.config.write(fp)
        self._load_plugins()

    def remove_all(self):
        for plugin in self.PLUGINS_DICT:
            self.remove_plugin(plugin)
            LOG.warning(
                "Plugin '{}' has been successfully removed".format(plugin))

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


class InfraredPlugin(object):
    PLUGIN_SPEC_FILE = 'plugin.spec'

    # PLUGIN_DIRS = dict(
    #     settings='settings',
    #     modules='library',
    #     roles='roles',
    #     playbooks='playbooks'
    # )

    def __init__(self, plugin_dir):
        """InfraredPlugin initializer

        :param plugin_dir: A path to the plugin's root dir
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
            raise IRFailedToAddPlugin(
                "Path to plugin dir '{}' doesn't exist".format(plugin_dir))
        self._path = full_path

    @property
    def vars_dir(self):
        return os.path.join(self.path, 'vars')

    @property
    def defaults_dir(self):
        return os.path.join(self.path, 'defaults')

    @property
    def playbook(self):
        """Plugin's main playbook"""
        return os.path.join(self.path, MAIN_PLAYBOOK)

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
        self._config = self.spec_validator(plugin_spec)

    @property
    def name(self):
        subparsers = self.config['subparsers']
        plugins = subparsers.keys()
        if len(plugins) != 1:
            # TODO(aopincar): Replace with a proper infrared exception
            raise Exception("Only one plugin should be defined in spec")
        return plugins[0]

    @property
    def type(self):
        return self.config['plugin_type']

    @property
    def description(self):
        return self.config['description']

    @staticmethod
    def spec_validator(spec_file):
        """Loads & validates that spec (YAML) file has all required fields

        :param spec_file: Path to plugin's spec file
        :raise IRFailedToAddPlugin: when mandatory data is missing in spec file
        :return: Dictionary with data loaded from a spec (YAML) file
        """
        if not os.path.isfile(spec_file):
            raise IRFailedToAddPlugin(
                "Plugin spec doesn't exist: {}".format(spec_file))
        import yaml
        with open(spec_file) as fp:
            spec_dict = yaml.load(fp)

        if not isinstance(spec_dict, dict):
            raise IRFailedToAddPlugin(
                "Spec file is empty or corrupted: '{}'".format(spec_file))

        for required_key in ('plugin_type', 'description'):
            if required_key not in spec_dict:
                raise IRFailedToAddPlugin(
                    "Required key '{}' is missing in plugin spec "
                    "file: {}".format(required_key, spec_file))
            if not isinstance(spec_dict[required_key], str):
                raise IRFailedToAddPlugin(
                    "Value of 'str' is expected for key '{}' in spec "
                    "file '{}'".format(required_key, spec_file))
            if not len(spec_dict[required_key]):
                raise IRFailedToAddPlugin(
                    "String value of key '{}' in spec file '{}' can't "
                    "be empty.".format(required_key, spec_file))

        key = 'subparsers'
        if key not in spec_dict:
            raise IRFailedToAddPlugin(
                "'{}' key is missing in spec file: '{}'".format(
                    key, spec_file))
        if not isinstance(spec_dict[key], dict):
            raise IRFailedToAddPlugin(
                "Value of '{}' in spec file '{}' should be "
                "'dict' type".format(key, spec_file))
        if len(spec_dict[key]) != 1:
            raise IRFailedToAddPlugin(
                "One subparser should be defined under '{}' in "
                "spec file '{}'".format(key, spec_file))
        if not isinstance(spec_dict[key].values()[0], dict):
            raise IRFailedToAddPlugin(
                "Subparser '{}' should be 'dict' type and not '{}' type in "
                "spec file '{}'".format(
                    spec_dict[key].keys()[0],
                    type(spec_dict[key].values()[0]), spec_file))
        if spec_dict[key].keys()[0].lower() == 'all':
            raise IRFailedToAddPlugin(
                "Adding a plugin named 'all' isn't allowed")

        return spec_dict

    def __repr__(self):
        return self.name
