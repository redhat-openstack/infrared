"""Service locator for the IR services

Stores and resolves all the dependencies for the services.
"""
import os
import sys

from infrared.core.services import workspaces
from infrared.core.services import plugins
from infrared.core.services import ansible_config
from infrared.core.services import execution_logger
from infrared.core.utils import logger

LOG = logger.LOG


class ServiceName(object):
    """Holds the supported services names. """
    WORKSPACE_MANAGER = "workspace_manager"
    PLUGINS_MANAGER = "plugins_manager"
    ANSIBLE_CONFIG_MANAGER = "ansible_config_manager"
    EXECUTION_LOGGER_MANAGER = "execution_logger_manager"


class CoreSettings(object):
    """
    Holds the main settings for the infrared.
    """

    def __init__(self, workspaces_base_folder=None,
                 plugins_conf_file=None,
                 install_plugin_at_start=True,
                 plugins_base_folder=None):
        """
        :param workspaces_base_folder: folder where the
        workspace will be stored
        :param plugins_conf_file: location of the plugins.ini file with the
        list of all plugins and types.
        :param install_plugin_at_start: specifies whether all the plugins
        should be installed on ir start. Skip installation may be required for
        unit tests, for example.
        """

        # todo(obaranov) replace with
        # todo(obaranov) os.path.join(os.path.expanduser("~"), '.infrared')
        # todo(obaranov) once IR is packaged as pip
        self.infrared_home = os.path.abspath(os.environ.get(
            "IR_HOME", os.getcwd()))

        # todo(obaranov) replace .workspaces to workspaces and .plugins.ini to
        # todo(obaranov) plugins.ini once IR is packaged as pip
        self.plugins_conf_file = plugins_conf_file or os.path.join(
            self.infrared_home, '.plugins.ini')
        self.workspaces_base_folder = workspaces_base_folder or os.path.join(
            self.infrared_home, '.workspaces')
        self.install_plugin_at_start = install_plugin_at_start
        self.plugins_base_folder = plugins_base_folder or os.path.join(
            self.infrared_home, 'plugins')


class CoreServices(object):
    """Holds and configures all the required for core services. """

    _SERVICES = {}

    @classmethod
    def setup(cls, core_settings=None):
        """
        Creates configuration from file or from defaults.

        :param core_settings: the instance of the CoreSettings class with the
        desired settings. If None is provided then the default settings
        will be used.
        """

        if core_settings is None:
            core_settings = CoreSettings()

        # create workspace manager
        if ServiceName.WORKSPACE_MANAGER not in cls._SERVICES:
            cls.register_service(ServiceName.WORKSPACE_MANAGER,
                                 workspaces.WorkspaceManager(
                                     core_settings.workspaces_base_folder))

        # create plugins manager
        if ServiceName.PLUGINS_MANAGER not in cls._SERVICES:
            # A temporary WH to skip all plugins installation on first InfraRed
            # command if the command is 'infrared plugin add'.
            # Should be removed together with auto plugins installation
            # mechanism.
            skip_plugins_install = {'plugin', 'add'}.issubset(sys.argv)
            cls.register_service(
                ServiceName.PLUGINS_MANAGER, plugins.InfraredPluginManager(
                    plugins_conf=core_settings.plugins_conf_file,
                    install_plugins=(core_settings.install_plugin_at_start and
                                     not skip_plugins_install),
                    plugins_dir=core_settings.plugins_base_folder))

        # create ansible config manager
        if ServiceName.ANSIBLE_CONFIG_MANAGER not in cls._SERVICES:
            cls.register_service(ServiceName.ANSIBLE_CONFIG_MANAGER,
                                 ansible_config.AnsibleConfigManager(
                                     core_settings.infrared_home))

        # create execution logger manager
        if ServiceName.EXECUTION_LOGGER_MANAGER not in cls._SERVICES:
            # get ansible manager
            ansible_manager = CoreServices.ansible_config_manager()
            # build log file path
            log_file = \
                os.path.join(core_settings.infrared_home, 'ir-commands.log')
            cls.register_service(ServiceName.EXECUTION_LOGGER_MANAGER,
                                 execution_logger.ExecutionLoggerManager(
                                     ansible_manager.ansible_config_path,
                                     log_file=log_file))

    @classmethod
    def register_service(cls, service_name, service):
        """Protect the _SERVICES dict"""
        CoreServices._SERVICES[service_name] = service

    @classmethod
    def _get_service(cls, name):
        if name not in cls._SERVICES:
            cls.setup()
        return cls._SERVICES[name]

    @classmethod
    def workspace_manager(cls):
        """Gets the workspace manager. """
        return cls._get_service(ServiceName.WORKSPACE_MANAGER)

    @classmethod
    def plugins_manager(cls):
        """Gets the plugin manager. """
        return cls._get_service(ServiceName.PLUGINS_MANAGER)

    @classmethod
    def ansible_config_manager(cls):
        """Gets the ansible config manager. """
        return cls._get_service(ServiceName.ANSIBLE_CONFIG_MANAGER)

    @classmethod
    def execution_logger_manager(cls):
        """Gets the execution logger manager. """
        return cls._get_service(ServiceName.EXECUTION_LOGGER_MANAGER)
