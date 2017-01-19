import ConfigParser
from os import path

import pytest
import yaml

from infrared import api
from infrared.core.services import plugins
import tests
from tests.test_profile import profile_manager_fixture, test_profile  # noqa


def subdict_in_dict(subdict, superdict):
    """True is subdict in subdict_in_dict. Else False.

    >>> subdict_in_dict({"k1": "v1"}, {"k1": "v1"})
    True
    >>> subdict_in_dict({"k1": "v1"}, {"k1": "v1", "k2": "v2"})
    True
    >>> subdict_in_dict({}, {"k1": "v1"})
    True
    >>> subdict_in_dict({"k1": "v1"}, {})
    False
    """
    return all(item in superdict.items()
               for item in subdict.items())


@pytest.fixture(scope="session")
def spec_fixture():
    """Generates plugin spec for testing, using tests/example plugin dir. """
    plugin_dir = path.join(path.abspath(path.dirname(tests.__file__)),
                           'example')
    test_plugin = plugins.InfraRedPlugin(plugin_dir=plugin_dir)
    from infrared.api import InfraRedPluginsSpec
    spec = InfraRedPluginsSpec(test_plugin)
    yield spec


def test_execute_no_profile(spec_fixture, profile_manager_fixture):   # noqa
    """Verify new profile was been created when there are no profiles. """

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    input_string = ['example']
    spec_manager.run_specs(args=input_string)
    assert profile_manager_fixture.get_active_profile()


def test_execute_fail(spec_fixture, profile_manager_fixture,          # noqa
                      test_profile):
    """Verify execution fails as expected with CLI input. """

    input_string = ['example', "--foo-bar", "fail"]

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)

    # Assert return code != 0
    assert return_value

    assert not path.exists(path.join(inventory_dir, output_file))


def test_execute_main(spec_fixture, profile_manager_fixture,          # noqa
                      test_profile):
    """Verify execution runs the main.yml playbook.

    Implicitly covers that vars dict is passed, since we know it will fail
    on task "fail if no vars dict" because test_test_execute_fail verifies
    failure is respected and output file isn't generated.

    Verifies that plugin roles are invoked properly.
    """

    input_string = ['example']

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))
    assert not path.exists(path.join(inventory_dir, "role_" + output_file))

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value == 0
    assert path.exists(path.join(inventory_dir, output_file))
    assert path.exists(path.join(
        inventory_dir,
        "role_" + output_file)), "Plugin role not invoked"


def test_fake_inventory(spec_fixture, profile_manager_fixture,          # noqa
                        test_profile):
    """Verify "--inventory" updates profile's inventory. """

    input_string = ['example', '--inventory', 'fake']

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    with pytest.raises(IOError) as exc:
        spec_manager.run_specs(args=input_string)
    assert exc.value.message == "File not found: fake"


def test_bad_user_inventory(spec_fixture, profile_manager_fixture,   # noqa
                            test_profile, tmpdir):
    """Verify user-inventory is loaded and not default inventory.

    tests/example/main.yml playbook runs on all hosts. New inventory defines
    unreachable node.
    """

    fake_inventory = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    fake_inventory.write("host2")
    test_profile.inventory = str(fake_inventory)

    input_string = ['example', '--inventory', str(fake_inventory)]

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)
    assert return_value == 3


@pytest.mark.parametrize("input_value", ["explicit", ""])  # noqa
def test_nested_value_CLI(spec_fixture,
                          profile_manager_fixture,
                          test_profile, input_value, tmpdir):
    """Tests that CLI input of Complex type Value is nested in vars dict.

    Use "-o output_file" and evaluate output YAML file.
    """

    dry_output = tmpdir.mkdir("tmp").join("dry_output.yml")

    if input_value:
        input_string = ['example', '--foo-bar', input_value]
    else:
        input_string = ['example']

    input_string.extend(["-o", str(dry_output)])

    # if no input, check that default value is loaded
    expected_output_dict = {"foo": {"bar": input_value or "default string"}}

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value == 0
    assert path.exists(path.join(inventory_dir, output_file))

    output_dict = yaml.load(dry_output.read())["provision"]
    # asserts expected_output_dict is subset of output
    assert subdict_in_dict(
        expected_output_dict,
        output_dict), "expected:{} actual:{}".format(expected_output_dict,
                                                     output_dict)


@pytest.mark.parametrize("input_args, expected_output_dict",       # noqa
                         [
                             # No spaces
                             (["--extra-vars=key=val"],
                              {"key": "val"}),
                             # Single var
                             (["--extra-vars", "key=val"],
                              {"key": "val"}),
                             # multiple usage
                             (["--extra-vars", "key=val",
                               "-e", "another.key=val1",
                               "-e", "another.key2=val2"],
                              {"key": "val",
                               "another": {"key": "val1",
                                           "key2": "val2"}}),
                             # nested vars
                             (["--extra-vars", "nested.key=val"],
                              {"nested": {"key": "val"}}),
                             # Mixed with spec input
                             (["--foo-bar", "val1",
                               "--extra-vars", "provision.foo.key=val2"],
                              {"provision": {"foo": {"bar": "val1",
                                                     "key": "val2"}}}),
                         ])
def test_extra_vars(spec_fixture,
                    profile_manager_fixture,
                    test_profile, input_args, expected_output_dict, tmpdir):
    """Tests that "--extra-vars" are inserted to vars_dict. """

    dry_output = tmpdir.mkdir("tmp").join("dry_output.yml")

    input_string = ['example'] + input_args + ["-o", str(dry_output),
                                               "--dry-run"]

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)

    # dry run returns None
    assert return_value is None

    output_dict = yaml.load(dry_output.read())
    # asserts expected_output_dict is subset of output
    assert subdict_in_dict(
        expected_output_dict,
        output_dict), "expected:{} actual:{}".format(expected_output_dict,
                                                     output_dict)


@pytest.mark.parametrize("input_args, file_dicts, expected_output_dict",       # noqa
                         [
                             # No spaces
                             (["--extra-vars=@dict_file"],
                              [{"filename": "dict_file",
                                "content": {"key": "val"}}],
                              {"key": "val"}),
                             # Single var
                             (["--extra-vars", "@dict_file"],
                              [{"filename": "dict_file",
                                "content": {"key": "val"}}],
                              {"key": "val"}),
                             # multiple usage
                             (["--extra-vars", "key=val",
                               "-e", "another.key=val1",
                               "-e", "another.key2=val2",
                               "--extra-vars", "@dict_file1",
                               "--extra-vars", "@dict_file2"],
                              [{"filename": "dict_file1",
                                "content": {"file-key": "file-val"}},
                               {"filename": "dict_file2",
                                "content": {"file-key-list": ["a", "b"]}}],
                              {"key": "val",
                               "another": {"key": "val1",
                                           "key2": "val2"},
                               "file-key": "file-val",
                               "file-key-list": ["a", "b"]}),
                             # Mixed with spec input
                             (["--foo-bar", "val1",
                               "--extra-vars", "@dict_file"],
                              [{"filename": "dict_file",
                                "content":
                                    {"provision": {"foo": {"key": "val2"}}}}],
                              {"provision": {"foo": {"bar": "val1",
                                                     "key": "val2"}}}),
                         ])
def test_extra_vars_with_file(spec_fixture,
                              profile_manager_fixture,
                              test_profile, input_args,
                              file_dicts, expected_output_dict, tmpdir):
    """Tests that extra-vars supports yaml file with "@". """

    tmp_dir = tmpdir.mkdir("tmp")
    dry_output = tmp_dir.join("dry_output.yml")
    for file_dict in file_dicts:
        tmp_file = tmp_dir.join(file_dict["filename"])
        # write dict to tmp yaml file
        with open(str(tmp_file), 'wb') as yaml_file:
            yaml_file.write(yaml.safe_dump(file_dict["content"],
                                           default_flow_style=False))
        # Inject full file path to command
        for i, arg in enumerate(input_args):
            input_args[i] = arg.replace(file_dict["filename"],
                                        str(tmp_file))

    input_string = ['example'] + input_args + ["-o", str(dry_output),
                                               "--dry-run"]

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)

    # dry run returns None
    assert return_value is None

    output_dict = yaml.load(dry_output.read())
    # asserts expected_output_dict is subset of output
    assert subdict_in_dict(
        expected_output_dict,
        output_dict), "expected:{} actual:{}".format(expected_output_dict,
                                                     output_dict)


@pytest.mark.parametrize("input_value, expected_output_dict", [  # noqa
    # DEFAULT style
    [
        ['--dictionary-val', "option1:value1"],
        {"dictionary": {"val": {"option1": "value1"}}}
    ],
    [
        ['--dictionary-val=option1:value1,option2:value2'],
        {"dictionary": {"val": {"option1": "value1",
                                "option2": "value2"}}}
    ],
    [
        ['--dictionary-val', 'option1:value1,option2:value2'],
        {"dictionary": {"val": {"option1": "value1",
                                "option2": "value2"}}}
    ],
    [
        ['--dictionary-val', 'my-nice.key:some_value,option2:value2'],
        {"dictionary": {"val": {"my-nice.key": "some_value",
                                "option2": "value2"}}}
    ],
])
def test_nested_KeyValueList_CLI(spec_fixture,
                                 profile_manager_fixture,
                                 test_profile, tmpdir,
                                 input_value, expected_output_dict):
    """Tests that CLI input of Complex type KeyValueList is nested in vars dict.

    Use "-o output_file" and evaluate output YAML file.
    """

    dry_output = tmpdir.mkdir("tmp").join("dry_output.yml")

    input_string = ['example'] + input_value

    input_string.extend(["-o", str(dry_output)])

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value == 0
    assert path.exists(path.join(inventory_dir, output_file))

    output_dict = yaml.load(dry_output.read())["provision"]
    # asserts expected_output_dict is subset of output
    assert subdict_in_dict(
        expected_output_dict,
        output_dict), "expected:{} actual:{}".format(expected_output_dict,
                                                     output_dict)


@pytest.mark.parametrize("bad_input", [  # noqa
    "keyNoVal", "bad-input",       # Key, no sign, no value, no sep
    "KeyNoValSign2:",              # Key, sign2 (':'), no value, no sep
    "KeyNoValOtherSign@",          # Key, other sign, no val, no spe
    ":value",                      # No key, sign2 (':'), value
    "key:val,",                    # End with separator1 (',')
    "ke*y:val", "key:v@al",        # Invalid sign in key & val - default style
    "k1:v1;k2:v2*blabla",          # All input should be match - default style
    "blabla(k1:v1;k2:v2",          # All input should be match - default style
    "k1:v1;blabla~k2:v2",          # All input should be match - default style
])
def test_nested_KeyValueList_negative(
        spec_fixture, profile_manager_fixture, test_profile, bad_input):
    """Tests that bad input for KeyValueList raises exception. """

    input_string = list(('example', "--dry-run", "--dictionary-val"))
    input_string.append(bad_input)

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)

    from infrared.core.utils import exceptions
    with pytest.raises(exceptions.IRKeyValueListException):
        spec_manager.run_specs(args=input_string)


@pytest.mark.parametrize("input_value", [               # noqa
    ["explicit", "--dry-run"],
    ["", "--dry-run"],
    ["explicit"],
    [""],
])
def test_nested_value_dry_run(spec_fixture,
                              profile_manager_fixture,
                              test_profile, input_value):
    """Verifies that --dry-run doesn't run playbook. """

    dry = "--dry-run" in input_value

    if input_value:
        input_string = ['example', '--foo-bar'] + input_value
    else:
        input_string = ['example']

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value is None if dry else return_value == 0
    # assert that playbook didn't run if "--dry-run" requested
    assert not dry == path.exists(
        path.join(inventory_dir, output_file))


@pytest.mark.parametrize("input_value", ["explicit", ""])  # noqa
def test_nested_value_CLI_with_answers_file(spec_fixture, tmpdir,
                                            profile_manager_fixture,
                                            test_profile, input_value):
    """Verfies answers file is loaded and that CLI overrides it.

    Use "-o output_file" and evaluate output YAML file.
    """
    mytempdir = tmpdir.mkdir("tmp")
    dry_output = mytempdir.join("dry_output.yml")

    config = ConfigParser.ConfigParser()
    config.add_section('example')
    config.set('example', 'foo-bar', 'from_answers_file')

    answers_file = mytempdir.join("answers_file")

    with open(str(answers_file), 'wb') as configfile:
        config.write(configfile)

    input_string = ['example', '--from-file', str(answers_file)]
    if input_value:
        input_string += ['--foo-bar', input_value]
    input_string.extend(["-o", str(dry_output)])

    # if no input, check that default value is loaded
    expected_output_dict = {"foo": {"bar": input_value or 'from_answers_file'}}

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value == 0
    assert path.exists(path.join(inventory_dir, output_file))

    output_dict = yaml.load(dry_output.read())["provision"]
    # asserts expected_output_dict is subset of output
    assert subdict_in_dict(
        expected_output_dict,
        output_dict), "expected:{} actual:{}".format(expected_output_dict,
                                                     output_dict)


def test_generate_answers_file(spec_fixture, profile_manager_fixture,  # noqa
                               test_profile, tmpdir):
    """Verify answers-file is generated to destination. """

    answers_file = tmpdir.mkdir("tmp").join("answers_file")
    input_string = ['example', '--generate-answers-file', str(answers_file)]

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)
    assert return_value is None

    config = ConfigParser.ConfigParser()
    config.read(str(answers_file))
    assert config.get("example", "foo-bar") == "default string"

    # verify playbook didn't run
    output_file = "output.example"
    inventory_dir = test_profile.path
    assert not path.exists(path.join(inventory_dir, output_file))


def test_ansible_args(spec_fixture, profile_manager_fixture,          # noqa
                      test_profile):
    """Verify execution runs with --ansible-args. """

    input_string = ['example', '--ansible-args',
                    'start-at-task="Test output";tags=only_this']

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_profile.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    profile_manager_fixture.activate(test_profile.name)
    return_value = spec_manager.run_specs(args=input_string)
    assert return_value == 0

    # Combination of tags and start-at-task should avoid the file creation
    assert not path.exists(path.join(inventory_dir, output_file))
