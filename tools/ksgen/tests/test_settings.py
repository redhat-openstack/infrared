"""
Usage:
    python test_tree.py <method_name>
    py.test test_tree.py [options]
"""

import os

import docopt
import pytest
from unittest import TestCase
import yaml

from test_utils import TEST_DIR, main
from ksgen.settings import load_configuration
from ksgen.settings import Generator


SETTINGS_DIR = os.path.join(TEST_DIR, "data", "settings")


def test_invalid_yml():
    path = os.path.join(TEST_DIR, 'data', 'yml-syntax')

    yaml_path = os.path.join(path, 'dashes.yml')
    with pytest.raises(yaml.scanner.ScannerError):
        load_configuration(yaml_path)

    yaml_path = os.path.join(path, 'spaces.yml')
    with pytest.raises(yaml.parser.ParserError):
        load_configuration(yaml_path)

    yaml_path = os.path.join(path, 'tab.yml')
    with pytest.raises(yaml.scanner.ScannerError):
        load_configuration(yaml_path)

    yaml_path = os.path.join(path, 'map.yml')
    with pytest.raises(TypeError):
        load_configuration(yaml_path)


class TestGenerator(TestCase):

    def setUp(self):
        """Create Generator object. """
        args = ['--provisioner=openstack', os.devnull]
        self.obj = Generator(config_dir=SETTINGS_DIR,
                             args=args)

    def test__prepare_defaults(self):
        provisioner_defaults = {
            "site": "cloud1",
            "topology": "all-in-one"
        }

        site_defaults = {
            "user": "user1"
        }

        self.obj.parsed = docopt.docopt(self.obj._doc_string,
                                        options_first=True, argv=self.obj.args)
        self.obj._prepare_defaults()

        for key, val in provisioner_defaults.iteritems():
            opt = "--provisioner-" + key
            assert self.obj.parsed[opt] == val

        assert (self.obj.parsed["--provisioner-site-user"] ==
                site_defaults["user"])


if __name__ == '__main__':
    main(locals())
