from os import path
import pytest

from infrared.core.services import plugins
import tests
from tests.test_profile import profile_manager_fixture, test_profile  # noqa


@pytest.fixture(scope="session")
def loaded_plugins():
    plugin_dir = path.join(path.abspath(path.dirname(tests.__file__)),
                           'example')
    test_plugin = plugins.InfraRedPlugin(plugin_dir=plugin_dir)
    from infrared.api import InfraRedGroupedPluginsSpec
    spec = InfraRedGroupedPluginsSpec(
        action_type=test_plugin.config["plugin_type"],
        description=test_plugin.config["description"],
        plugins={test_plugin.name: test_plugin}
    )
    yield spec


def test_execute_no_profile(loaded_plugins, profile_manager_fixture):   # noqa
    """Verify execution fails without an active profile. """
    from infrared.core.utils import exceptions
    with pytest.raises(exceptions.IRNoActiveProfileFound):
        loaded_plugins.spec_handler(None, args={'command0': 'example'})


def test_execute_main(loaded_plugins, profile_manager_fixture,          # noqa
                      test_profile):
    """Verify execution runs the main.yml playbook. """

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    loaded_plugins.spec_handler(None, args={'command0': 'example'})
    assert path.exists(path.join(inventory_dir, output_file))
