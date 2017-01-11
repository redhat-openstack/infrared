"""Service locator for the IR services

Stores and resolves all the dependencies for the services.
"""
import os

try:  # py2
    import ConfigParser
except ImportError:  # py3
    import configparser as ConfigParser

from infrared.core.services import profiles
from infrared.core.services import plugins
from infrared.core.utils import logger

LOG = logger.LOG


class ServiceName(object):
    """Holds the supported services names. """
    PROFILE_MANAGER = "profile_manager"
    PLUGINS_MANAGER = "plugins_manager"


class CoreServices(object):
    """Holds and configures all the required for core services. """

    _SERVICES = {}
    DEFAULTS = {
        'profiles_base_folder': '.profiles',
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
            os.path.abspath(config.get(section, 'profiles_base_folder')),
            os.path.abspath(config.get(section, 'plugins_conf_file'))
        )

    @classmethod
    def _configure(cls, profile_dir, plugins_conf):
        """Register services to manager. """

        # create profile manager
        if ServiceName.PROFILE_MANAGER not in CoreServices._SERVICES:
            cls.register_service(ServiceName.PROFILE_MANAGER,
                                 profiles.ProfileManager(profile_dir))
        # create plugins manager
        if ServiceName.PLUGINS_MANAGER not in CoreServices._SERVICES:
            cls.register_service(ServiceName.PLUGINS_MANAGER,
                                 plugins.InfraRedPluginManager(plugins_conf))

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
    def profile_manager(cls):
        """Gets the profile manager. """
        return cls._get_service(ServiceName.PROFILE_MANAGER)

    @classmethod
    def plugins_manager(cls):
        """Gets the plugin manager. """
        return cls._get_service(ServiceName.PLUGINS_MANAGER)
