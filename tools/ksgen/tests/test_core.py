"""
Usage:
    python test_core.py <method_name>
    py.test test_core.py [options]
"""

import docopt
import os
import pytest

from ksgen import core
from test_utils import TEST_DIR, main

SETTINGS_DIR = os.path.join(TEST_DIR, "data", "settings")


@pytest.yield_fixture
def os_environ():
    """Backups "KHALEESI_DIR" from os.environ and restores it at teardown. """
    backup_flag = False
    if "KHALEESI_DIR" in os.environ:
        backup_flag = True
        backup_value = os.environ.get("KHALEESI_DIR")
    yield os.environ
    if backup_flag:
        os.environ["KHALEESI_DIR"] = backup_value


def fake_config_cli(**kwargs):
    """Generates a docopt.Dict object. """

    def convert_to_cli(opt):
        return "--" + opt.replace("_", "-")

    args = {convert_to_cli(k): v for k, v in kwargs.iteritems()}
    return docopt.Dict(args)


def test_get_config_dir(os_environ):

    # Negative - Missing input
    with pytest.raises(ValueError) as exc:
        core.get_config_dir(fake_config_cli(config_dir=None))
    assert "Missing path" in str(exc.value)

    # Negative - Bad path
    with pytest.raises(ValueError) as exc:
        core.get_config_dir(fake_config_cli(config_dir="/fake/path"))
    assert "Bad path" in str(exc.value)
    assert "/fake/path" in str(exc.value)

    # verify CLI
    assert core.get_config_dir(
        fake_config_cli(config_dir=SETTINGS_DIR)) == SETTINGS_DIR

    # Verify ENV
    os.environ["KHALEESI_SETTINGS"] = SETTINGS_DIR
    assert core.get_config_dir(
        fake_config_cli(config_dir=None)) == SETTINGS_DIR

    # Verify CLI over ENV
    os.environ["KHALEESI_SETTINGS"] = "/fake/env/path"
    assert core.get_config_dir(
        fake_config_cli(config_dir=SETTINGS_DIR)) == SETTINGS_DIR


if __name__ == '__main__':
    main(locals())
