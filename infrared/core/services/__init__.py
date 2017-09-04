"""Service locator for the IR services

Stores and resolves all the dependencies for the services.
"""
import os

try:  # py2
    import ConfigParser
except ImportError:  # py3
    import configparser as ConfigParser

from infrared.core.settings import IR_DIR
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
        ws_base_folder = os.path.expanduser(config.get(section, 'workspaces_base_folder'))
        if not os.path.isabs(ws_base_folder):
            ws_base_folder = os.path.abspath(os.path.join(IR_DIR, ws_base_folder))

        plugins_conf_file = os.path.expanduser(config.get(section, 'plugins_conf_file'))
        if not os.path.isabs(plugins_conf_file):
            plugins_conf_file = os.path.abspath(os.path.join(IR_DIR, plugins_conf_file))

        config.read(file_path)
        cls._configure(
            ws_base_folder,
            plugins_conf_file
        )

    @classmethod
    def _configure(cls, workspace_dir, plugins_conf):
        """Register services to manager. """

        # create workspace manager
        if ServiceName.WORKSPACE_MANAGER not in CoreServices._SERVICES:
            cls.register_service(ServiceName.WORKSPACE_MANAGER,
                                 workspaces.WorkspaceManager(workspace_dir))
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
