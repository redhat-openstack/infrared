"""Service locator for the IR services

Stores and resolves all the dependencies for the services.
"""
import os

from infrared.core.services import dependency
from infrared.core.services import workspaces
from infrared.core.services import plugins
from infrared.core.utils import logger

LOG = logger.LOG


class ServiceName(object):
    """Holds the supported services names. """
    WORKSPACE_MANAGER = "workspace_manager"
    PLUGINS_MANAGER = "plugins_manager"
    DEPENDENCY_MANAGER = "dependency_manager"


class CoreSettings(object):
    """
    Holds the main settings for the infrared.
    """

    def __init__(self, workspaces_base_folder=None,
                 plugins_conf_file=None,
                 install_plugin_at_start=True,
                 library_base_folder=None):
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
        infarared_home = os.path.abspath(os.environ.get(
            "INFRARED_HOME", os.getcwd()))

        # todo(obaranov) replace .workspaces to workspaces and .plugins.ini to
        # todo(obaranov) plugins.ini once IR is packaged as pip
        self.plugins_conf_file = plugins_conf_file or os.path.join(
            infarared_home, '.plugins.ini')
        self.workspaces_base_folder = workspaces_base_folder or os.path.join(
            infarared_home, '.workspaces')
        self.install_plugin_at_start = install_plugin_at_start
        self.library_base_folder = library_base_folder or os.path.join(
            infarared_home, '.library')


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

        # create dependency manager for plugins
        if ServiceName.DEPENDENCY_MANAGER not in cls._SERVICES:
            cls.register_service(ServiceName.DEPENDENCY_MANAGER,
                                 dependency.PluginDependencyManager(
                                     core_settings.library_base_folder))

        # create plugins manager
        if ServiceName.PLUGINS_MANAGER not in cls._SERVICES:
            cls.register_service(
                ServiceName.PLUGINS_MANAGER, plugins.InfraredPluginManager(
                    plugins_conf=core_settings.plugins_conf_file,
                    dependencies_manager=CoreServices.dependency_manager(),
                    install_plugins=core_settings.install_plugin_at_start))

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
    def dependency_manager(cls):
        """Gets the plugin manager. """
        return cls._get_service(ServiceName.DEPENDENCY_MANAGER)
