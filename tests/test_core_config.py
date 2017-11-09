import os
from infrared.core.services import CoreServices, CoreSettings


def test_infrared_home_dir(tmpdir):
    # set INFRARED_HOME
    new_home = str(tmpdir.mkdir("ir_home"))
    os.environ['INFRARED_HOME'] = new_home

    # init infrared core
    test_settings = CoreSettings()
    test_settings.install_plugin_at_start = False
    CoreServices.setup(test_settings)

    assert os.path.isdir(new_home)
    assert os.path.isdir(os.path.join(new_home, '.workspaces'))
    assert os.path.isfile(os.path.join(new_home, '.plugins.ini'))


