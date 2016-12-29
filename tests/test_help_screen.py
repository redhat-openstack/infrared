from cStringIO import StringIO
import os
import sys

import pytest

from infrared.main import main as ir_main
from tests.test_plugins import SAMPLE_PLUGINS_DIR
from tests.test_plugins import get_plugin_spec_flatten_dict
from tests.test_plugins import plugins_conf_fixture
from tests.test_plugins import plugin_manager_fixture


def test_list_yamls_in_help_screen(plugin_manager_fixture):
    """Tests that __LISTYAMLS__ placeholder works

    '__LISTYAMLS__' placeholder in help field of spec's option should be
    replaced with a list pf available YAML files
    :param plugin_manager_fixture: Fixture object which yields
    InfraRedPluginManger object
    """

    plugin_manager = plugin_manager_fixture()
    plugin_dir = os.path.join(SAMPLE_PLUGINS_DIR,
                              'help_screen_plugin_with_list_yamls')
    plugin_dict = get_plugin_spec_flatten_dict(plugin_dir)

    plugin_manager.add_plugin(plugin_dir)

    help_cmd = ['ir', plugin_dict['name'], '--help']
    # Also replaces sys.argv[0] from 'pytest' to 'ir'
    sys.argv = help_cmd
    sys.stdout = mystdout = StringIO()

    try:
        # argparse raises SystemExit after printing help screen
        with pytest.raises(SystemExit) as ex:
            ir_main()
        assert ex.value.code == 0, \
            "Return code of help cmd '{}' is {}".format(
                ' '.join(help_cmd), ex.code)
    finally:
        sys.stdout = sys.__stdout__

    with open(os.path.join(plugin_dir, 'expected_output.txt')) as fp:
        expected_str = fp.read()
        rtrn_str = mystdout.getvalue()
        # Removes 'StringIO' object reference from return string
        returned_str = rtrn_str[:rtrn_str.rfind('<StringIO.StringIO instance')]
        assert returned_str == expected_str
