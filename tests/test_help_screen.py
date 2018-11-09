from six.moves import cStringIO as StringIO
import os
import sys

import pytest

from infrared.main import main as ir_main
from tests.test_plugins import SAMPLE_PLUGINS_DIR
from tests.test_plugins import get_plugin_spec_flatten_dict
from tests.test_plugins import plugins_conf_fixture  # noqa
from tests.test_plugins import plugin_manager_fixture  # noqa


def test_list_yamls_in_help_screen(plugin_manager_fixture):  # noqa
    """Tests that __LISTYAMLS__ placeholder works

    '__LISTYAMLS__' placeholder in help field of spec's option should be
    replaced with a list pf available YAML files
    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """

    topology_help = """  --topology TOPOLOGY   help of topology option
                        Available values: {}""".format(
        list(set(['undercloud', 'compute']))
    )
    topology_network_help = """  --topology-networks TOPOLOGY-NETWORKS
                        help of topology-networks option
                        Available values: {}""".format(
        list(set(['3_nics', '2_nics', '1_nics']))
    )

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

    rtrn_str = mystdout.getvalue()
    returned_str = rtrn_str[:rtrn_str.rfind('<StringIO.StringIO instance')]

    assert topology_help in returned_str
    assert topology_network_help in returned_str
