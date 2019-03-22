from six.moves import configparser
from os import path

import pytest
import yaml

from infrared import api
from infrared.core.services import plugins
import tests
from tests.test_workspace import workspace_manager_fixture, test_workspace  # noqa


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
    test_plugin = plugins.InfraredPlugin(plugin_dir=plugin_dir)
    from infrared.api import InfraredPluginsSpec
    spec = InfraredPluginsSpec(test_plugin)
    yield spec


def test_execute_no_workspace(spec_fixture, workspace_manager_fixture):   # noqa
    """Verify new workspace was been created when there are no workspaces. """

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    input_string = ['example']
    spec_manager.run_specs(args=input_string)
    assert workspace_manager_fixture.get_active_workspace()


def test_execute_fail(spec_fixture, workspace_manager_fixture,          # noqa
                      test_workspace):
    """Verify execution fails as expected with CLI input. """

    input_string = ['example', "--foo-bar", "fail"]

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    # Assert return code != 0
    assert return_value

    assert not path.exists(path.join(inventory_dir, output_file))


def test_execute_main(spec_fixture, workspace_manager_fixture,          # noqa
                      test_workspace):
    """Verify execution runs the main.yml playbook.

    Implicitly covers that vars dict is passed, since we know it will fail
    on task "fail if no vars dict" because test_test_execute_fail verifies
    failure is respected and output file isn't generated.

    Verifies that plugin roles are invoked properly.
    """

    input_string = ['example']

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))
    assert not path.exists(path.join(inventory_dir, "role_" + output_file))

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value == 0
    assert path.exists(path.join(inventory_dir, output_file))
    assert path.exists(path.join(
        inventory_dir,
        "role_" + output_file)), "Plugin role not invoked"


def test_fake_inventory(spec_fixture, workspace_manager_fixture,          # noqa
                        test_workspace):
    """Verify "--inventory" updates workspace's inventory. """

    input_string = ['example', '--inventory', 'fake']

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    workspace_manager_fixture.activate(test_workspace.name)
    from infrared.core.utils import exceptions
    with pytest.raises(exceptions.IRFileNotFoundException) as exc:
        spec_manager.run_specs(args=input_string)
    assert "fake" in exc.value.message


def test_bad_user_inventory(spec_fixture, workspace_manager_fixture,   # noqa
                            test_workspace, tmpdir):
    """Verify user-inventory is loaded and not default inventory.

    tests/example/main.yml playbook runs on all hosts. New inventory defines
    unreachable node.
    """

    fake_inventory = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    fake_inventory.write("host2")
    test_workspace.inventory = str(fake_inventory)

    input_string = ['example', '--inventory', str(fake_inventory)]

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)
    assert return_value


@pytest.mark.parametrize("input_value", ["explicit", ""])  # noqa
def test_nested_value_CLI(spec_fixture,
                          workspace_manager_fixture,
                          test_workspace, input_value, tmpdir):
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

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value == 0
    assert path.exists(path.join(inventory_dir, output_file))

    output_dict = yaml.safe_load(dry_output.read())["provision"]
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
                             # No spaces with val also having "="
                             (["--extra-vars=key=val="],
                              {"key": "val="}),
                             # Single var
                             (["--extra-vars", "key=val"],
                              {"key": "val"}),
                             # Single var with val also having "="
                             (["--extra-vars", "key=val="],
                              {"key": "val="}),
                             # multiple usage
                             (["--extra-vars", "key=val",
                               "-e", "another.key=val1",
                               "-e", "another.key2=val2",
                               "-e", "another.key3=val3="],
                              {"key": "val",
                               "another": {"key": "val1",
                                           "key2": "val2",
                                           "key3": "val3="}}),
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
                    workspace_manager_fixture,
                    test_workspace, input_args, expected_output_dict, tmpdir):
    """Tests that "--extra-vars" are inserted to vars_dict. """

    dry_output = tmpdir.mkdir("tmp").join("dry_output.yml")

    input_string = ['example'] + input_args + ["-o", str(dry_output),
                                               "--dry-run"]

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    # dry run returns None
    assert return_value is None

    output_dict = yaml.safe_load(dry_output.read())
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
                              workspace_manager_fixture,
                              test_workspace, input_args,
                              file_dicts, expected_output_dict, tmpdir):
    """Tests that extra-vars supports yaml file with "@". """

    tmp_dir = tmpdir.mkdir("tmp")
    dry_output = tmp_dir.join("dry_output.yml")
    for file_dict in file_dicts:
        tmp_file = tmp_dir.join(file_dict["filename"])
        # write dict to tmp yaml file
        with open(str(tmp_file), 'w+') as yaml_file:
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

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    # dry run returns None
    assert return_value is None

    output_dict = yaml.safe_load(dry_output.read())
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
                                 workspace_manager_fixture,
                                 test_workspace, tmpdir,
                                 input_value, expected_output_dict):
    """Tests that CLI input of Complex type KeyValueList is nested in vars dict.

    Use "-o output_file" and evaluate output YAML file.
    """

    dry_output = tmpdir.mkdir("tmp").join("dry_output.yml")

    input_string = ['example'] + input_value

    input_string.extend(["-o", str(dry_output)])

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value == 0
    assert path.exists(path.join(inventory_dir, output_file))

    output_dict = yaml.safe_load(dry_output.read())["provision"]
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
        spec_fixture, workspace_manager_fixture, test_workspace, bad_input):
    """Tests that bad input for KeyValueList raises exception. """

    input_string = list(('example', "--dry-run", "--dictionary-val"))
    input_string.append(bad_input)

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    workspace_manager_fixture.activate(test_workspace.name)

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
                              workspace_manager_fixture,
                              test_workspace, input_value):
    """Verifies that --dry-run doesn't run playbook. """

    dry = "--dry-run" in input_value

    if input_value:
        input_string = ['example', '--foo-bar'] + input_value
    else:
        input_string = ['example']

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value is None if dry else return_value == 0
    # assert that playbook didn't run if "--dry-run" requested
    assert not dry == path.exists(
        path.join(inventory_dir, output_file))


@pytest.mark.parametrize("input_value", ["explicit", ""])  # noqa
def test_nested_value_CLI_with_answers_file(spec_fixture, tmpdir,
                                            workspace_manager_fixture,
                                            test_workspace, input_value):
    """Verfies answers file is loaded and that CLI overrides it.

    Use "-o output_file" and evaluate output YAML file.
    """
    mytempdir = tmpdir.mkdir("tmp")
    dry_output = mytempdir.join("dry_output.yml")

    config = configparser.ConfigParser()
    config.add_section('example')
    config.set('example', 'foo-bar', 'from_answers_file')

    answers_file = mytempdir.join("answers_file")

    with open(str(answers_file), 'w+') as configfile:
        config.write(configfile)

    input_string = ['example', '--from-file', str(answers_file)]
    if input_value:
        input_string += ['--foo-bar', input_value]
    input_string.extend(["-o", str(dry_output)])

    # if no input, check that default value is loaded
    expected_output_dict = {"foo": {"bar": input_value or 'from_answers_file'}}

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value == 0
    assert path.exists(path.join(inventory_dir, output_file))

    output_dict = yaml.safe_load(dry_output.read())["provision"]
    # asserts expected_output_dict is subset of output
    assert subdict_in_dict(
        expected_output_dict,
        output_dict), "expected:{} actual:{}".format(expected_output_dict,
                                                     output_dict)


def test_generate_answers_file(spec_fixture, workspace_manager_fixture,  # noqa
                               test_workspace, tmpdir):
    """Verify answers-file is generated to destination. """

    answers_file = tmpdir.mkdir("tmp").join("answers_file")
    input_string = \
        ['example', '--generate-answers-file', str(answers_file), '--dry-run']

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)
    assert return_value is None

    config = configparser.ConfigParser()
    config.read(str(answers_file))
    assert config.get("example", "foo-bar") == "default string"

    # verify playbook didn't run
    output_file = "output.example"
    inventory_dir = test_workspace.path
    assert not path.exists(path.join(inventory_dir, output_file))


def test_ansible_args(spec_fixture, workspace_manager_fixture,          # noqa
                      test_workspace):
    """Verify execution runs with --ansible-args. """

    input_string = ['example', '--ansible-args',
                    'start-at-task="Test output";tags=only_this']

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    inventory_dir = test_workspace.path
    output_file = "output.example"
    assert not path.exists(path.join(inventory_dir, output_file))

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)
    assert return_value == 0

    # Combination of tags and start-at-task should avoid the file creation
    assert not path.exists(path.join(inventory_dir, output_file))


@pytest.mark.parametrize("cli_args, from_file, expected_output", [    # noqa
    # Tests CLI (no section)
    ("--iniopt opt1=val1",
     None,
     {'opt1': 'val1'}),

    # Tests CLI
    ("--iniopt sec1.opt1=val1",
     None,
     {'sec1': {'opt1': 'val1'}}),

    # Tests CLI (multiple args)
    ("--iniopt sec1.opt1=val1 --iniopt sec1.opt2=val2",
     None,
     {'sec1': {'opt1': 'val1', 'opt2': 'val2'}}),

    # Tests from-file
    (None,
     'tests/example/files/answers_file.ini',
     {'sec1': {'opt1': 'f_val1', 'opt2': 'f_val2'},
      'sec2': {'opt1': 'f_val3'}}),

    # Tests CLI with from-file
    ("--iniopt secx.optx=valx",
     'tests/example/files/answers_file.ini',
     {'secx': {'optx': 'valx'}}),
])
def test_output_with_IniType(spec_fixture, tmpdir,
                             workspace_manager_fixture, test_workspace,
                             cli_args, from_file, expected_output):
    """Verifies the output file with IniType complex type args from CLI & file
    """
    my_temp_dir = tmpdir.mkdir("tmp")
    dry_output = my_temp_dir.join("dry_output.yml")

    input_string = ['example', "--dry-run", "-o", str(dry_output)]

    if from_file:
        input_string += ['--from-file', from_file]

    if cli_args:
        input_string += cli_args.split()

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value is None
    assert path.exists(dry_output.strpath),\
        "Output file doesn't exit: {}".format(dry_output.strpath)

    with open(dry_output.strpath) as fp:
        loaded_yml = yaml.safe_load(fp)
        assert loaded_yml['provision']['iniopt'] == expected_output


@pytest.mark.parametrize("cli_args, from_file, expected_output", [    # noqa
    # Tests CLI (no section)
    ("--nestedlist opt1=val1",
     None,
     [{'opt1': 'val1'}]),

    # Tests CLI
    ("--nestedlist sec1.opt1=val1",
     None,
     [{'sec1': {'opt1': 'val1'}}]),

    # Tests CLI (multiple args)
    ("--nestedlist sec1.opt1=val1,sec1.opt2=val2",
     None,
     [{'sec1': {'opt1': 'val1','opt2': 'val2'}}]),
])
def test_output_with_NestedList(spec_fixture, tmpdir,
                             workspace_manager_fixture, test_workspace,
                             cli_args, from_file, expected_output):
    """Verifies the output file with NestedList complex type args
       from CLI & file
    """
    my_temp_dir = tmpdir.mkdir("tmp")
    dry_output = my_temp_dir.join("dry_output.yml")

    input_string = ['example', "--dry-run", "-o", str(dry_output)]

    if from_file:
        input_string += ['--from-file', from_file]

    if cli_args:
        input_string += cli_args.split()

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value is None
    assert path.exists(dry_output.strpath),\
        "Output file doesn't exit: {}".format(dry_output.strpath)

    with open(dry_output.strpath) as fp:
        loaded_yml = yaml.safe_load(fp)
        assert loaded_yml['provision']['nestedlist'] == expected_output


@pytest.mark.parametrize("cli_args, from_file, expected_output", [    # noqa
    # Tests CLI (no section)
    ("--nestedlist-app opt1=val1",
     None,
     [{'opt1': 'val1'}]),

    # Tests CLI
    ("--nestedlist-app sec1.opt1=val1",
     None,
     [{'sec1': {'opt1': 'val1'}}]),

    # Tests CLI (multiple args)
    ("--nestedlist-app sec1.opt1=val1 --nestedlist-app sec1.opt2=val2",
     None,
     [{'sec1': {'opt1': 'val1'}}, {'sec1': {'opt2': 'val2'}}]),

    # Tests CLI (complex multiple args)
    ("--nestedlist-app sec1.opt1=val1,sec1.opt2=val2 \
        --nestedlist-app sec1.opt2=val3",
     None,
     [{'sec1': {'opt1': 'val1', 'opt2': 'val2'}}, {'sec1': {'opt2': 'val3'}}]),
])
def test_output_with_NestedList_app(spec_fixture, tmpdir,
                             workspace_manager_fixture, test_workspace,
                             cli_args, from_file, expected_output):
    """Verifies the output file with NestedList complex type args
       from CLI & file
    """
    my_temp_dir = tmpdir.mkdir("tmp")
    dry_output = my_temp_dir.join("dry_output.yml")

    input_string = ['example', "--dry-run", "-o", str(dry_output)]

    if from_file:
        input_string += ['--from-file', from_file]

    if cli_args:
        input_string += cli_args.split()

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    workspace_manager_fixture.activate(test_workspace.name)
    return_value = spec_manager.run_specs(args=input_string)

    assert return_value is None
    assert path.exists(dry_output.strpath),\
        "Output file doesn't exit: {}".format(dry_output.strpath)

    with open(dry_output.strpath) as fp:
        loaded_yml = yaml.safe_load(fp)
        assert loaded_yml['provision']['nestedlist']['app'] == expected_output


def test_deprecation(spec_fixture, workspace_manager_fixture,  # noqa
                               test_workspace, tmpdir):
    """Verify execution runs with deprecated option """

    my_temp_dir = tmpdir.mkdir("tmp")
    deprecated_output = my_temp_dir.join("deprecated_output.yml")

    deprecated_input_string = \
        ['example', '--deprecated-way', 'TestingValue', '--dry-run',
         '-o', str(deprecated_output)]

    output = my_temp_dir.join("output.yml")

    input_string = \
        ['example', '--new-way', 'TestingValue', '--dry-run',
         '-o', str(output)]

    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    workspace_manager_fixture.activate(test_workspace.name)
    spec_manager.run_specs(args=deprecated_input_string)
    spec_manager.run_specs(args=input_string)

    with open(deprecated_output.strpath) as fp:
        deprecated_yml = yaml.safe_load(fp)["provision"]

    with open(output.strpath) as fp:
        new_yml = yaml.safe_load(fp)["provision"]

    assert deprecated_yml.get('new', None).get('way', None) == 'TestingValue'
    assert new_yml.get('new', None).get('way', None) == 'TestingValue'
