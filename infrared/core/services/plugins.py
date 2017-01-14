from ConfigParser import ConfigParser
from collections import OrderedDict
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
    supported_types=dict(
        provision='Provisioning plugins',
        install='Installing plugins',
        test='Testing plugins'
    )
)
MAIN_PLAYBOOK = "main.yml"
BUILTIN_PLUGINS_PATH = "./plugins"
LOG = logger.LOG


class InfraRedPluginManager(object):

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
                    plugin = InfraRedPlugin(plugin_path)
                    self.__class__.PLUGINS_DICT[plugin_name] = plugin

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

        if init_plugins_conf:
            abspath = os.path.abspath(BUILTIN_PLUGINS_PATH)
            pldirs = [pd for pd in os.listdir(
                abspath) if os.path.isdir(os.path.join(abspath, pd))]
            for pldir in pldirs:
                self.add_plugin(os.path.join(abspath, pldir))

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
        :return: InfraRedPlugin instance
        """
        return cls.PLUGINS_DICT[plugin_name]

    def __iter__(self):
        for plugin in self.PLUGINS_DICT.iteritems():
            yield plugin
        else:
            raise StopIteration

    def add_plugin(self, plugin_path, dest=None):

        dest = dest or "plugins"
        destination = os.path.abspath(dest)
        if not os.path.exists(plugin_path):
            tmpdir = tempfile.mkdtemp(prefix="ir-")
            cwd = os.getcwdu()
            os.chdir(tmpdir)
            try:
                subprocess.check_output(["git", "clone", plugin_path])
            except subprocess.CalledProcessError:
                shutil.rmtree(tmpdir)
                raise IRFailedToAddPlugin(
                    "Cloning git repo {} is failed".format(plugin_path))
            cloned = os.listdir(tmpdir)
            plugin_dir_name = cloned[0]

            plugin_path = os.path.join(destination, plugin_dir_name)
            shutil.copytree(os.path.join(tmpdir, plugin_dir_name),
                            plugin_path)
            os.chdir(cwd)
            shutil.rmtree(tmpdir)

        plugin = InfraRedPlugin(plugin_path)
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

        self._install_requirements(plugin_path)
        self._load_plugins()

    def remove_plugin(self, plugin_type, plugin_name):
        if plugin_type not in self.config.options(
                self.SUPPORTED_TYPES_SECTION):
            raise IRFailedToRemovePlugin(
                "Unsupported plugin type: '{}'".format(plugin_type))
        elif not self.config.has_section(plugin_type):
            raise IRFailedToRemovePlugin(
                "There are no plugins of type '{}' installed".format(
                    plugin_type))
        elif not self.config.has_option(plugin_type, plugin_name):
            raise IRFailedToRemovePlugin(
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
            # TODO(aopincar): Replace with a proper InfraRed exception
            raise Exception("Only one plugin should be defined in spec")
        return plugins[0]

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

        return spec_dict

    def __repr__(self):
        return self.name
