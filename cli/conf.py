import ConfigParser

import exceptions
import os

from cli import utils
from cli import logger

LOG = logger.LOG

DEFAULT_SECTIONS = {
    'defaults': dict(
        settings='settings',
        modules='library',
        roles='roles',
        playbooks='playbooks'
    ),

    'provisioner':  dict(
        main_playbook='provision.yml',
        cleanup_playbook='cleanup.yml'
    ),

    'installer': dict(
        main_playbook='install.yml',
        cleanup_playbook='cleanup.yml'
    )
}


def load_config_file(file_path=None):
    """Load config file order(file_path, ENV, CWD, USER HOME, SYSTEM).

    :param file_path: the optional path to the configuration file to read.
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

    for path in (file_path, env_path, cwd_path, utils.USER_PATH, utils.SYSTEM_PATH):
        if path is not None and os.path.exists(path):
            _config.read(path)
            break
    else:
        LOG.warning("Configuration file not found, using InfraRed project dir")
        for section_name, section_data in DEFAULT_SECTIONS.items():
            _config.add_section(section_name)
            for option, value in section_data.items():
                _config.set(section_name, option, value)

    # Validates settings dir exists
    settings_dir = _config.get('defaults', 'settings')
    if not os.path.exists(settings_dir):
        raise exceptions.IRFileNotFoundException(
            settings_dir,
            "Settings directory doesn't exist: ")

    return _config
