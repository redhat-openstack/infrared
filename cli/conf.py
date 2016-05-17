import ConfigParser

import exceptions
import os

from cli import utils
from cli import logger

LOG = logger.LOG
DEFAULT_CONF_DIRS = dict(
    settings='settings',
    modules='library',
    roles='roles',
    playbooks='playbooks'
)


class ConfigWrapper(object):
    """
    The helper class for the InfraRed configuration.
    """
    _DEFAULT_SECTION = 'defaults'

    @classmethod
    def load_config_file(cls):
        """Load config file order(ENV, CWD, USER HOME, SYSTEM).

        :return ConfigParser: config object
        """

        # create a parser with default path to InfraRed's main dir
        cwd_path = os.path.join(os.getcwd(), utils.IR_CONF_FILE)
        _config = ConfigParser.ConfigParser()

        env_path = os.getenv(utils.ENV_VAR_NAME, None)
        if env_path is not None:
            env_path = os.path.expanduser(env_path)
            if os.path.isdir(env_path):
                env_path = os.path.join(env_path, utils.IR_CONF_FILE)

        for path in (env_path, cwd_path, utils.USER_PATH, utils.SYSTEM_PATH):
            if path is not None and os.path.exists(path):
                _config.read(path)
                break
        else:
            LOG.warning(
                "Configuration file not found, using InfraRed project dir")
            project_dir = os.path.dirname(os.path.dirname(__file__))

            _config.add_section('defaults')
            for option, value in DEFAULT_CONF_DIRS.iteritems():
                _config.set('defaults', option,
                            os.path.join(project_dir, value))

        return ConfigWrapper(_config)

    def __init__(self, conf):
        self.config = conf
        self.validate()

    def get_settings_dirs(self, section=_DEFAULT_SECTION):
        """
        Returns the list of the configured settings folders.
        """
        return self.config.get(section, 'settings').split(
            os.pathsep)

    def get_modules_dir(self, section=_DEFAULT_SECTION):
        """
        Gets the modules directory.
        """
        return self.config.get(section, 'modules')

    def get_playbooks_dir(self, section=_DEFAULT_SECTION):
        """
        Gets the playbooks directory.
        """
        return self.config.get(section, 'playbooks')

    def build_app_settings_dirs(self, app_name):
        return [os.path.join(path, app_name)
                for path in self.get_settings_dirs()]

    def validate(self):
        """
        Validates the configuration.
        """
        # Validates at least one settings dir exists
        dirs = self.get_settings_dirs()
        if not any([os.path.exists(path) for path in dirs]):
            raise exceptions.IRFileNotFoundException(
                dirs,
                "Settings directories do not exist: ")

    def sections(self):
        """
        Gets the list of sections
        """
        return self.config.sections()

    def get_spec_config(self, spec_name):
        """
        Gets the spec configuration from the config file.
        """

        return self.config.items(spec_name)

config = ConfigWrapper.load_config_file()
