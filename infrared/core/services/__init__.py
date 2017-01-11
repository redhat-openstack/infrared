"""Service locator for the IR services

Stores and resolves all the dependencies for the services.
"""
import os

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
    def init(cls, file_path=None):
        """Creates configuration from file or from defaults. """
        if not file_path or not os.path.exists(file_path):
            LOG.info("Configuration file was not found/provided. "
                     "Configuring with the defaults settings.")
            cls.from_dict()
        else:
            cls.from_ini_file(file_path)

    @classmethod
    def from_dict(cls, conf_dict=None):
        """Configures services using the default settings.

        Check the CoreServices.DEFAULTS for the dict structure.
        """
        if conf_dict is None:
            conf_dict = cls.DEFAULTS
        cls._configure(
            os.path.abspath(conf_dict['profiles_base_folder']),
            os.path.abspath(conf_dict['plugins_conf_file'])
        )

    @classmethod
    def from_ini_file(cls, config_file, section='core'):
        """Reads core conf and configures all the required services. """
        import ConfigParser
        config = ConfigParser.ConfigParser()
        config.read(config_file)

        cls.from_dict(dict(
            profiles_base_folder=config.get(section, 'profiles_base_folder'),
            plugins_conf_file=config.get(section, 'plugins_conf_file')))

    @classmethod
    def _configure(cls, profile_dir, plugins_conf):
        """Register services to manager. """

        # create profile manager
        if ServiceName.PROFILE_MANAGER not in CoreServices._SERVICES:
            cls.register_service(ServiceName.PROFILE_MANAGER,
                                 profiles.ProfileManager(profile_dir))
        # create plugins manager
        if ServiceName.PLUGINS_MANAGER not in CoreServices._SERVICES:
            # check default config location if plugin conf is not provided
            if plugins_conf is None:
                plugins_conf = os.path.join(
                    os.path.dirname(os.getcwd()),
                    cls.DEFAULTS['plugins_conf_file'])
                LOG.warning("Plugin conf file hasn't been given,"
                            "trying to load it from the"
                            "default path: '{}'".format(plugins_conf))

            cls.register_service(ServiceName.PLUGINS_MANAGER,
                                 plugins.InfraRedPluginManager(plugins_conf))

    @classmethod
    def register_service(cls, service_name, service):
        """Protect the _SERVICES dict"""
        CoreServices._SERVICES[service_name] = service

    @classmethod
    def _get_service(cls, name):
        if name not in cls._SERVICES:
            cls.from_dict()
        return cls._SERVICES[name]

    @classmethod
    def profile_manager(cls):
        """Gets the profile manager. """
        return cls._get_service(ServiceName.PROFILE_MANAGER)

    @classmethod
    def plugins_manager(cls):
        """Gets the plugin manager. """
        return cls._get_service(ServiceName.PLUGINS_MANAGER)
