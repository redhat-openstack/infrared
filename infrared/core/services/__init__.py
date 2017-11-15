"""Service locator for the IR services

Stores and resolves all the dependencies for the services.
"""
import os

try:  # py2
    import ConfigParser
except ImportError:  # py3
    import configparser as ConfigParser

from infrared.core.services import workspaces
from infrared.core.services import plugins
from infrared.core.utils import logger

LOG = logger.LOG


class ServiceName(object):
    """Holds the supported services names. """
    WORKSPACE_MANAGER = "workspace_manager"
    PLUGINS_MANAGER = "plugins_manager"


class CoreServices(object):
    """Holds and configures all the required for core services. """

    _SERVICES = {}
    DEFAULTS = {
        'workspaces_base_folder': '.workspaces',
        'plugins_conf_file': '.plugins.ini'
    }

    @classmethod
    def setup(cls, file_path='infrared.cfg', section='core'):
        """Creates configuration from file or from defaults. """

        config = ConfigParser.SafeConfigParser(defaults=cls.DEFAULTS)
        config.add_section(section)

        # if file not found no exception will be raised
        config.read(file_path)
        cls._configure(
            os.path.abspath(config.get(section, 'workspaces_base_folder')),
        )

    @classmethod
    def _configure(cls, workspace_dir):
        """Register services to manager. """

        # create workspace manager
        if ServiceName.WORKSPACE_MANAGER not in CoreServices._SERVICES:
            cls.register_service(ServiceName.WORKSPACE_MANAGER,
                                 workspaces.WorkspaceManager(workspace_dir))
        workspace_manager = cls._get_service(ServiceName.WORKSPACE_MANAGER)
        active_workspace = workspace_manager.get_active_workspace()

        if not active_workspace and not workspace_manager.list():
            active_workspace = workspace_manager.create()
            workspace_manager.activate(active_workspace.name)
            LOG.warn("There are no workspaces. New workspace added: %s",
                     active_workspace.name)

        if active_workspace:
            plugins_conf = os.path.join(active_workspace.path,
                                        cls.DEFAULTS['plugins_conf_file'])
        else:
            plugins_conf = ""

        # create plugins manager
        if ServiceName.PLUGINS_MANAGER not in CoreServices._SERVICES:
            cls.register_service(ServiceName.PLUGINS_MANAGER,
                                 plugins.InfraredPluginManager(plugins_conf))

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
