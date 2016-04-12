import ConfigParser
import os

import pytest
from cli import exceptions
from cli import spec
from cli.spec import ValueArgument, YamlFileArgument


@pytest.mark.parametrize("res_args, options, req_args, nonreq_args", [
    [{'host': spec.ValueArgument(),
      'command0': 'virsh',
      'ssh-user': spec.ValueArgument()},
     {
         'host': {'help': 'help', 'required': True},
         'ssh-user': {'help': 'help2', 'required': True},
         'ssh-key': {'help': 'help3', 'default': 'id_rsa'}
     }, ['host', 'ssh-user'], ['ssh-key']],
])
def test_required_option_exception(res_args,
                                   options,
                                   req_args,
                                   nonreq_args):

    with pytest.raises(exceptions.IRConfigurationException) as ex_info:
        spec.override_default_values(res_args, options)

    for arg in req_args:
        assert arg in ex_info.value.message

    for arg in nonreq_args:
        assert arg not in ex_info.value.message


@pytest.mark.parametrize("res_args, options, expected_args", [
    # data set #1
    [{'host': None,
      'command0': 'virsh',
      'from-file': {
          'virsh': {
              'host': 'earth',
          }
      },
      'ssh-user': 'root',
      'ssh-key': None},
     {'virsh': {
         'host': {'help': 'help', 'required': True},
         'ssh-user': {'help': 'help2', 'required': True},
         'ssh-key': {'help': 'help3', 'required': True, 'default': 'id_rsa'}
     }},
     {'host': 'earth',
      'command0': 'virsh',
      'from-file': {
          'virsh': {
              'host': 'earth',
          }
      },
      'ssh-user': 'id_rsa'}],

    # todo(yfried): enable this in the future
    # [{'host': None,
    #   'command0': 'virsh',
    #   'from-file': {
    #       'virsh': {
    #           'host': 'earth',
    #       }
    #   },
    #   'ssh-user': None,
    #   'ssh-key': None},
    #  {'virsh': {
    #      'opt1': {'requires_only': ['host']},
    #      'host': {'help': 'help', 'required': True},
    #      'ssh-user': {'help': 'help2', 'required': True},
    #      'ssh-key': {'help': 'help3', 'required': True, 'default': 'id_rsa'}
    #  }},
    #  {'host': 'earth',
    #   'command0': 'virsh',
    #   'from-file': {
    #       'virsh': {
    #           'host': 'earth',
    #       }
    #   },
    #   'ssh-user': 'id_rsa'}]
])
def test_required_options_are_set(res_args,
                                  options,
                                  expected_args):
    actual_args = spec.override_default_values(res_args, options)
    cmp(actual_args, expected_args)


@pytest.mark.parametrize('test_value', [
  'test string', 1, 0.1
])
def test_value_argument_compare(test_value):
    val = ValueArgument(test_value)

    # verify several equality checks
    assert val == test_value
    assert val in [test_value, ]

    # negative case
    val = ValueArgument(0)
    assert val != test_value
    assert val not in [test_value, ]


def test_yamls_file_locations(tmpdir):
    """
    Verify IR is looking for correct file locations.
    """
    subcommand = "virsh"

    # create mock settings structure
    app_dir = tmpdir.mkdir("installer")
    app_spec_dir = app_dir.mkdir(subcommand)
    file1 = app_dir.mkdir("arg1").mkdir("arg2").join("test_load2.yml")
    file2 = app_spec_dir.mkdir("arg1").mkdir("arg2").join("test_load1.yml")
    file1.write("""---
    network:
        ip: 1
    """)
    file2.write("""---
    network:
        ip: 2
    """)

    locations = YamlFileArgument.get_file_locations(
        app_dir.strpath, subcommand, "arg1-arg2")

    assert len(locations) == 3
    assert locations[0] == file2.dirname
    assert locations[1] == file1.dirname
    assert locations[2] == "."

    files = YamlFileArgument.get_allowed_files(
        app_dir.strpath, subcommand, "arg1-arg2")

    assert len(files) == 2
    assert files[0] == file2.strpath
    assert files[1] == file1.strpath
