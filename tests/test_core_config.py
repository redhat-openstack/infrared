import os
import pytest
from infrared.core.services import CoreServices, CoreSettings


@pytest.fixture
def infrared_home(tmpdir):
    new_home = str(tmpdir.mkdir("ir_home"))
    os.environ['IR_HOME'] = new_home
    yield new_home
    del os.environ['IR_HOME']


def test_infrared_home_dir(infrared_home):
    os.environ['ANSIBLE_CONFIG'] = os.path.join(infrared_home, 'ansible.cfg')
    test_settings = CoreSettings()
    test_settings.install_plugin_at_start = False
    CoreServices.setup(test_settings)

    assert os.path.isdir(infrared_home)
    assert os.path.isdir(os.path.join(infrared_home, '.workspaces'))
    assert os.path.isfile(os.path.join(infrared_home, '.plugins.ini'))
    assert os.path.isdir(os.path.join(infrared_home, 'plugins'))
    assert os.path.isfile(os.path.join(infrared_home, 'ansible.cfg'))
    assert CoreServices.workspace_manager().workspace_dir == os.path.join(
        infrared_home, '.workspaces')
    assert CoreServices.plugins_manager().config_file == os.path.join(
        infrared_home, '.plugins.ini')
    assert CoreServices.plugins_manager().plugins_dir == os.path.join(
        infrared_home, 'plugins')
    assert CoreServices.ansible_config_manager().ansible_config_path == os.path.join(
        infrared_home, 'ansible.cfg')
