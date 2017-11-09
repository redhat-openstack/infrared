"""Service locator for the IR services

Stores and resolves all the dependencies for the services.
"""
import os

from infrared.core.services import workspaces
from infrared.core.services import plugins
from infrared.core.utils import logger

LOG = logger.LOG


class ServiceName(object):
    """Holds the supported services names. """
    WORKSPACE_MANAGER = "workspace_manager"
    PLUGINS_MANAGER = "plugins_manager"


class CoreSettings(object):
    """
    Holds the main settings for the infrared.
    """

    def __init__(self, workspaces_base_folder=None,
                 plugins_conf_file=None,
                 install_plugin_at_start=True):
        """
        :param workspaces_base_folder: folder where the
        workspace will be stored
        :param plugins_conf_file: location of the plugins.ini file with the
        list of all plugins and types.
        :param install_plugin_at_start: specifies whether all the plugins
        should be installed on ir start. Skip installation mya be required for
        unit tests, for example.
        """

        # for now by default use current folder
        # todo(obaranov) replace with
        # os.path.join(os.path.expanduser("~"), '.infrared') once we are ready
        # formigration
        infarared_home = os.environ.get(
            "INFRARED_HOME", os.path.abspath(os.getcwd()))

        self.plugins_conf_file = plugins_conf_file or os.path.join(
            infarared_home, '.plugins.ini')
        self.workspaces_base_folder = workspaces_base_folder or os.path.join(
            infarared_home, '.workspaces')
        self.install_plugin_at_start = install_plugin_at_start


class CoreServices(object):
    """Holds and configures all the required for core services. """

    _SERVICES = {}

    @classmethod
    def setup(cls, core_settings=None):
        """Creates configuration from file or from defaults. """

        if core_settings is None:
            core_settings = CoreSettings()

        # create workspace manager
        if ServiceName.WORKSPACE_MANAGER not in CoreServices._SERVICES:
            cls.register_service(ServiceName.WORKSPACE_MANAGER,
                                 workspaces.WorkspaceManager(
                                     core_settings.workspaces_base_folder))
        # create plugins manager
        if ServiceName.PLUGINS_MANAGER not in CoreServices._SERVICES:
            cls.register_service(
                ServiceName.PLUGINS_MANAGER, plugins.InfraredPluginManager(
                    plugins_conf=core_settings.plugins_conf_file,
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
