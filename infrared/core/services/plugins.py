from ConfigParser import ConfigParser
from collections import OrderedDict
import os
import shutil
import tempfile
import yaml
import git

# TODO(aopincar): Add pip to the project's requirements
import pip

from infrared.core.utils import logger
from infrared.core.utils.exceptions import IRFailedToAddPlugin
from infrared.core.utils.exceptions import IRFailedToRemovePlugin
from infrared.core.utils.exceptions import IRUnsupportedPluginType

DEFAULT_PLUGIN_INI = dict(
    supported_types=OrderedDict([
        ('provision', 'Provisioning plugins'),
        ('install', 'Installing plugins'),
        ('test', 'Testing plugins'),
        ('other', 'Other type plugins'),
    ])
)


MAIN_PLAYBOOK = "main.yml"
PLUGINS_DIR = os.path.abspath("./plugins")
LOG = logger.LOG

with open(os.path.join(PLUGINS_DIR, "registry.yaml"), "r") as fo:
    PLUGINS_REGISTRY = yaml.load(fo)


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

    def get_installed_plugins(self, plugins_type=None):
        """Returns a dict with all installed plugins

        The return dictionary contains all installed plugins with their
        descriptions & categorized by plugin type.

        :param plugins_type: A specific type of plugins to return
        """
        plugins_dict = OrderedDict()

        for supported_type in self.supported_plugin_types:
            if plugins_type:
                if plugins_type != supported_type:
                    continue
                elif plugins_type not in self.supported_plugin_types:
                    raise IRUnsupportedPluginType(plugins_type)

            if not self.config.has_section(supported_type):
                continue
            else:
                plugins_dict[supported_type] = {}

            for plugin_name in self.config.options(supported_type):
                plugin_desc = self.PLUGINS_DICT[plugin_name].description

                plugins_dict[supported_type][plugin_name] = plugin_desc

        if plugins_type:
            return plugins_dict.get(plugins_type, {})

        return plugins_dict

    def get_all_plugins(self):
        """Returns a dict with all available plugins

        The return dictionary contains all available plugins (installed & not
        installed) with their descriptions & categorized by plugin type.
        """
        type_based_plugins_dict = self.get_installed_plugins()
        installed_plugins_set = \
            set([plugin_name for plugins_of_type in
                 type_based_plugins_dict.values() for plugin_name in
                 plugins_of_type])

        for plugin_name in PLUGINS_REGISTRY.keys():
            if plugin_name not in installed_plugins_set:
                plugin_type = PLUGINS_REGISTRY[plugin_name]['type']
                plugin_desc = PLUGINS_REGISTRY[plugin_name]['desc']
                if plugin_type not in type_based_plugins_dict:
                    type_based_plugins_dict[plugin_type] = {}
                type_based_plugins_dict[plugin_type][plugin_name] = plugin_desc

        return type_based_plugins_dict

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
    def _clone_git_plugin(git_url, repo_plugin_path=None, dest_dir=None):
        """Clone a plugin into a given destination directory

        :param git_url: Plugin's Git URL
        :param dest_dir: destination where to clone a plugin into (if 'source'
          is a Git URL)
        :param repo_plugin_path: path in the Git repo where the infrared plugin
          is defined
        :return: Path to plugin cloned directory (str)
        """
        dest_dir = os.path.abspath(dest_dir or "plugins")
        plugin_dir_name = os.path.split(git_url)[-1].split('.')[0]

        tmpdir = tempfile.mkdtemp(prefix="ir-")
        cwd = os.getcwdu()
        os.chdir(tmpdir)
        try:
            git.Repo.clone_from(url=git_url,
                                to_path=os.path.join(tmpdir, plugin_dir_name))
        except (git.exc.GitCommandError):
            shutil.rmtree(tmpdir)
            raise IRFailedToAddPlugin(
                "Cloning git repo {} is failed".format(git_url))

        plugin_source = os.path.join(dest_dir, plugin_dir_name)
        if os.path.exists(plugin_source):
            shutil.rmtree(plugin_source)
        shutil.copytree(os.path.join(tmpdir, plugin_dir_name),
                        plugin_source)

        if repo_plugin_path:
            plugin_source = plugin_source + '/' + repo_plugin_path

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
        plugin_data = {}
        # Check if a plugin is in the registry
        if plugin_source in PLUGINS_REGISTRY:
            plugin_data = PLUGINS_REGISTRY[plugin_source]
            plugin_source = PLUGINS_REGISTRY[plugin_source]['src']

        # Local dir plugin
        if os.path.exists(plugin_source):
            pass
        # Git Plugin
        else:
            plugin_src_path = plugin_data.get('src_path', '')
            plugin_source = self._clone_git_plugin(
                plugin_source, plugin_src_path,
                dest)

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
        try:
            return self.config['subparsers'][self.name]['description']
        except KeyError:
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

        plugin_type_key = 'plugin_type'
        if plugin_type_key not in spec_dict:
            raise IRFailedToAddPlugin(
                "Required key '{}' is missing in plugin spec "
                "file: {}".format(plugin_type_key, spec_file))
        if not isinstance(spec_dict[plugin_type_key], str):
            raise IRFailedToAddPlugin(
                "Value of 'str' is expected for key '{}' in spec "
                "file '{}'".format(plugin_type_key, spec_file))
        if not len(spec_dict[plugin_type_key]):
            raise IRFailedToAddPlugin(
                "String value of key '{}' in spec file '{}' can't "
                "be empty.".format(plugin_type_key, spec_file))

        subparsers_key = 'subparsers'
        if subparsers_key not in spec_dict:
            raise IRFailedToAddPlugin(
                "'{}' key is missing in spec file: '{}'".format(
                    subparsers_key, spec_file))
        if not isinstance(spec_dict[subparsers_key], dict):
            raise IRFailedToAddPlugin(
                "Value of '{}' in spec file '{}' should be "
                "'dict' type".format(subparsers_key, spec_file))
        if 'description' not in spec_dict \
                and 'description' not in spec_dict[subparsers_key].values()[0]:
            raise IRFailedToAddPlugin(
                "Required key 'description' is missing for supbarser '{}' in "
                "spec file '{}'".format(
                    spec_dict[subparsers_key].keys()[0], spec_file))
        if len(spec_dict[subparsers_key]) != 1:
            raise IRFailedToAddPlugin(
                "One subparser should be defined under '{}' in "
                "spec file '{}'".format(subparsers_key, spec_file))
        if not isinstance(spec_dict[subparsers_key].values()[0], dict):
            raise IRFailedToAddPlugin(
                "Subparser '{}' should be 'dict' type and not '{}' type in "
                "spec file '{}'".format(
                    spec_dict[subparsers_key].keys()[0],
                    type(spec_dict[subparsers_key].values()[0]), spec_file))
        if spec_dict[subparsers_key].keys()[0].lower() == 'all':
            raise IRFailedToAddPlugin(
                "Adding a plugin named 'all' isn't allowed")

        return spec_dict

    def __repr__(self):
        return self.name
