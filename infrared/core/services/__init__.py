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
INFRARED_DATA_DIR = os.path.abspath(".infrared" if os.path.isdir(
    ".infrared") else os.path.expanduser("~/.infrared"))


class ServiceName(object):
    """Holds the supported services names. """
    WORKSPACE_MANAGER = "workspace_manager"
    PLUGINS_MANAGER = "plugins_manager"


class CoreServices(object):
    """Holds and configures all the required for core services. """

    _SERVICES = {}
    DEFAULTS = {
        'workspaces_base_folder': os.path.join(INFRARED_DATA_DIR,
                                               'workspaces'),
        'plugins_conf_file': os.path.join(INFRARED_DATA_DIR, 'plugins.ini'),
        'plugins_dir': os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../../plugins")
    }

    @classmethod
    def setup(cls, file_path=os.path.join(INFRARED_DATA_DIR, 'infrared.cfg'),
              section='core'):
        """Creates configuration from file or from defaults. """

        config = ConfigParser.SafeConfigParser(defaults=cls.DEFAULTS)
        config.add_section(section)

        if not os.path.isdir(INFRARED_DATA_DIR):
            os.mkdir(INFRARED_DATA_DIR)

        # if file not found no exception will be raised
        config.read(file_path)
        cls._configure(
            os.path.abspath(config.get(section, 'workspaces_base_folder')),
            os.path.abspath(config.get(section, 'plugins_conf_file')),
            config.get(section, "plugins_dir")
        )

    @classmethod
    def _configure(cls, workspace_dir, plugins_conf, plugins_dir):
        """Register services to manager. """

        # create workspace manager
        if ServiceName.WORKSPACE_MANAGER not in CoreServices._SERVICES:
            cls.register_service(ServiceName.WORKSPACE_MANAGER,
                                 workspaces.WorkspaceManager(workspace_dir))
        # create plugins manager
        if ServiceName.PLUGINS_MANAGER not in CoreServices._SERVICES:
            cls.register_service(ServiceName.PLUGINS_MANAGER,
                                 plugins.InfraredPluginManager(
                                     plugins_conf, plugins_dir))

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
