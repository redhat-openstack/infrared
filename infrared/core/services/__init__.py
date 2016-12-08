"""Service locator for the IR services

Stores and resolves all the dependencies for the services.
"""
import os

from infrared.core.services import profiles


class CoreServices(object):
    """
    Holds and configures all the required for core services
    """

    SERVICES = {}

    DEFAULTS = {
        'profiles_base_folder': '.profiles',
    }

    @classmethod
    def form_defaults(cls):
        """
        Configures services using the default settings.
        """
        cls._configure(
            cls.DEFAULTS['profiles_base_folder']
            )

    @classmethod
    def from_ini_file(cls, config_file, section='core'):
        """
        Reads core configuration and configures all the required services.
        """
        import ConfigParser
        config = ConfigParser.ConfigParser()
        config.read(config_file)

        profile_dir = os.path.abspath(
            config.get(section, 'profiles_base_folder'))

        cls._configure(profile_dir)

    @classmethod
    def _configure(cls, profile_dir):
        cls.SERVICES['profile_manager'] = profiles.ProfileManager(profile_dir)

    @classmethod
    def _get_service(cls, name):
        if name not in cls.SERVICES:
            cls.form_defaults()
        return cls.SERVICES[name]

    @classmethod
    def profile_manager(cls):
        """
        Gets the profile manager
        """
        return cls._get_service('profile_manager')
