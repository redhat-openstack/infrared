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
    test_settings = CoreSettings()
    test_settings.install_plugin_at_start = False
    CoreServices.setup(test_settings)

    assert os.path.isdir(infrared_home)
    assert os.path.isdir(os.path.join(infrared_home, '.workspaces'))
    assert os.path.isdir(os.path.join(infrared_home, '.library'))
    assert os.path.isfile(os.path.join(infrared_home, '.plugins.ini'))
    assert CoreServices.workspace_manager().workspace_dir == os.path.join(
        infrared_home, '.workspaces')
    assert CoreServices.plugins_manager()._config_file == os.path.join(
        infrared_home, '.plugins.ini')
