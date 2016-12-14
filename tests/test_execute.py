from mock import patch
from os import path
import pytest


from infrared import api
from infrared.core.services import plugins
from infrared.core.services import CoreServices

import tests
from tests.test_profile import profile_manager_fixture, test_profile  # noqa


@pytest.fixture(scope="session")
def spec_fixture():
    plugin_dir = path.join(path.abspath(path.dirname(tests.__file__)),
                           'example')
    test_plugin = plugins.InfraRedPlugin(plugin_dir=plugin_dir)
    from infrared.api import InfraRedPluginsSpec
    spec = InfraRedPluginsSpec(test_plugin)
    yield spec


@patch.object(CoreServices, 'profile_manager')  # noqa
def test_execute_no_profile(test_profile_manager,
                            spec_fixture, profile_manager_fixture,
                            test_profile):
    test_profile_manager.return_value = profile_manager_fixture
    sm = api.SpecManager()
    sm.register_spec(spec_fixture)

    input_string = ['example']

    from infrared.core.utils import exceptions
    with pytest.raises(exceptions.IRNoActiveProfileFound):
        sm.run_specs(args=input_string)


@patch.object(CoreServices, 'profile_manager')  # noqa
def test_execute_main(test_profile_manager,
                      spec_fixture, profile_manager_fixture,
                      test_profile):
    input_string = ['example']
    test_profile_manager.return_value = profile_manager_fixture

    sm = api.SpecManager()
    sm.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    sm.run_specs(args=input_string)

    assert path.exists(path.join(inventory_dir, output_file))


@patch.object(CoreServices, 'profile_manager')  # noqa
def test_nested_value_CLI(test_profile_manager,
                          spec_fixture, profile_manager_fixture,
                          test_profile):
    input_string = ['example', '--foo-bar', 'value']
    expected_output_dict = {"foo": {"bar": "value"}}
    test_profile_manager.return_value = profile_manager_fixture

    from infrared import api
    sm = api.SpecManager()
    sm.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    sm.run_specs(args=input_string)

    import json
    with open(path.join(inventory_dir, output_file), 'r') as output:
        # asserts expected_output_dict is subset of output
        assert all(item in json.load(output).items()
                   for item in expected_output_dict.items())
