import os
from shutil import copyfile
from collections import OrderedDict
from ConfigParser import ConfigParser

from infrared.core.utils import logger

LOG = logger.LOG

DEFAULT_ANSIBLE_CONFIG = 'ansible.cfg.example'

DEFAULT_ANSIBLE_SETTINGS = dict(
    defaults=OrderedDict([
        ('host_key_checking', 'False'),
        ('forks', 500),
        ('timeout', 30),
        ('force_color', 1),
    ]),
)


class AnsibleConfigManager(object):

    def __init__(self, ansible_config_path):
        """
        :param ansible_config: A path to the ansible config
        """
        self.ansible_config_path = ansible_config_path

        if not os.path.isfile(self.ansible_config_path):
            self._create_ansible_config()

    def _create_ansible_config(self):
        """
        Create ansible config file
        :return:
        """

        LOG.warning("Ansible conf ('{}') not found, creating it with "
                    "default data".format(self.ansible_config_path))

        if os.path.isfile(os.path.join(os.getcwd(), DEFAULT_ANSIBLE_CONFIG)):
            copyfile(os.path.join(os.getcwd(), DEFAULT_ANSIBLE_CONFIG), self.ansible_config_path)
        else:
            with open(self.ansible_config_path, 'w') as fp:
                config = ConfigParser()

                for section, section_data in DEFAULT_ANSIBLE_SETTINGS.items():
                    if not config.has_section(section):
                        config.add_section(section)
                    for option, value in section_data.items():
                        config.set(section, option, value)

                config.write(fp)

    def inject_config(self):
        """
        Export the environment variable for config path, if variable doesn't exist.
        :return:
        """

        os.environ['ANSIBLE_CONFIG'] = self.ansible_config_path
