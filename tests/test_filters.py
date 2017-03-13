import os

import pytest

from tests.links.absolute_path import absolute_path


@pytest.mark.parametrize("target_dir, rel_dir, expected_return", [
    ("local_dir", None, os.path.join(os.getcwd(), "local_dir")),
    ("rel_dir", '/tmp', os.path.join('/tmp', "rel_dir")),
    ("", None, os.getcwd()),
    (None, None, os.getcwd()),
    ("~", None, os.path.expanduser('~')),
    ("~/home_dir", None, os.path.join(os.path.expanduser('~'), "home_dir")),
    ("/full/path/to/dir", None, '/full/path/to/dir'),
])
def test_absolute_path_filter(target_dir, rel_dir, expected_return):
    """Tests the absolute_path filter method

    :param target_dir: target_dir to be "absolutized"
    :param rel_dir: Replacement relative directory path
    :param expected_return: The expected return path from absolute_path filter
    """
    assert absolute_path(target_dir, rel_dir) == expected_return
