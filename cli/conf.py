import ConfigParser
import os
import time

from cli import exceptions

ENV_VAR_NAME = "IR_CONFIG"
IR_CONF_FILE = 'infrared.cfg'
CWD_PATH = os.path.join(os.getcwd(), IR_CONF_FILE)
USER_PATH = os.path.expanduser('~/.' + IR_CONF_FILE)
SYSTEM_PATH = os.path.join('/etc/infrared', IR_CONF_FILE)
YAML_EXT = ".yml"
TMP_OUTPUT_FILE = 'ir_settings_' + str(time.time()) + YAML_EXT
INFRARED_DIR_ENV_VAR = 'IR_SETTINGS'


def load_config_file():
    """Load config file order(ENV, CWD, USER HOME, SYSTEM).

    :return ConfigParser: config object
    """
    _config = ConfigParser.ConfigParser(allow_no_value=True)
    env_path = os.getenv(ENV_VAR_NAME, None)
    if env_path is not None:
        env_path = os.path.expanduser(env_path)
        if os.path.isdir(env_path):
            env_path = os.path.join(env_path, IR_CONF_FILE)
    for path in (env_path, CWD_PATH, USER_PATH, SYSTEM_PATH):
        if path is not None and os.path.exists(path):
            _config.read(path)
            return _config

    conf_file_paths = "\n".join([CWD_PATH, USER_PATH, SYSTEM_PATH])
    raise exceptions.IRFileNotFoundException(
        conf_file_paths,
        "IR configuration not found. "
        "Please set it in one of the following paths:\n")


config = load_config_file()

for dir_path in config.options('DEFAULTS'):
    globals()[dir_path.upper()] = config.get('DEFAULTS', dir_path)
