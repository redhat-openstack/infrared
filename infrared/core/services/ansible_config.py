import os
from collections import OrderedDict
from six.moves import configparser

from infrared.core.utils import logger
from infrared.core.utils.validators import AnsibleConfigValidator

LOG = logger.LOG

DEFAULT_ANSIBLE_SETTINGS = dict(
    defaults=OrderedDict([
        ('host_key_checking', 'False'),
        ('forks', 500),
        ('timeout', 30),
        ('pipelining', 'True'),
        ('force_color', 1),
        ('show_custom_stats', 'True'),
    ]),
)


class AnsibleConfigManager(object):

    def __init__(self, infrared_home):
        """
        :param ansible_config: A path to the ansible config
        """
        self.ansible_config_path = self._get_ansible_conf_path(infrared_home)
        config_validator = AnsibleConfigValidator()

        if not os.path.isfile(self.ansible_config_path):
            self._create_ansible_config()
        else:
            config_validator.validate_from_file(self.ansible_config_path)

    @staticmethod
    def _get_ansible_conf_path(infrared_home):
        """
        Check for Ansible config in specific locations
        and return the first located

        :param infrared_home: infrared's home directory
        :return:
        """
        locations_list = [
            os.path.join(os.getcwd(), 'ansible.cfg'),
            os.path.join(infrared_home, 'ansible.cfg'),
            os.path.join(os.path.expanduser('~'), '.ansible.cfg')
        ]

        env_var_path = os.environ.get('ANSIBLE_CONFIG', '')

        if env_var_path != '':
            return env_var_path

        for location in locations_list:
            if os.path.isfile(location):
                return location

        return os.path.join(infrared_home, 'ansible.cfg')

    def _create_ansible_config(self):
        """ Create ansible config file """

        LOG.warning("Ansible conf ('{}') not found, creating it with "
                    "default data".format(self.ansible_config_path))

        with open(self.ansible_config_path, 'w') as fp:
            config = configparser.ConfigParser()

            for section, section_data in DEFAULT_ANSIBLE_SETTINGS.items():
                if not config.has_section(section):
                    config.add_section(section)
                for option, value in section_data.items():
                    config.set(section, option, str(value))

            config.write(fp)

    def inject_config(self):
        """
        Export the environment variable for config path,
        if variable doesn't exist.

        """
        if os.environ.get('ANSIBLE_CONFIG', '') == '':
            os.environ['ANSIBLE_CONFIG'] = self.ansible_config_path
