import ConfigParser

import pytest
from cli import exceptions
from cli import spec


def mock_cmd_line_method(monkeypatch, res_args, options):
    monkeypatch.setattr(spec,
                        "_get_command_line_args",
                        value=lambda x, y, z: (res_args, options))


@pytest.mark.parametrize("res_args, options, req_args, nonreq_args", [
    # data set #1
    [{'host': None,
      'command0': 'virsh',
      'from-file': {
          'virsh': {
              'host': 'earth',
          }
      },
      'ssh-user': None},
     {'virsh': {
         'host': {'help': 'help', 'required': True},
         'ssh-user': {'help': 'help2', 'required': True},
         'ssh-key': {'help': 'help3', 'default': 'id_rsa'}
     }
     }, ['ssh-user'], ['host', 'ssh-key']],

    # data set #2
    [{'host': None,
      'command0': 'virsh',
      'ssh-user': None},
     {'virsh': {
         'host': {'help': 'help', 'required': True},
         'ssh-user': {'help': 'help2', 'required': True},
         'ssh-key': {'help': 'help3', 'default': 'id_rsa'}
     }
     }, ['host', 'ssh-user'], ['ssh-key']],

    # data set #3 (require_only)
    [{'host': None,
      'command0': 'virsh',
      'ssh-user': None,
      'req_only_opt': True},
     {'virsh': {
         'host': {'help': 'help', 'required': True},
         'ssh-user': {'help': 'help2', 'required': True},
         'ssh-key': {'help': 'help3', 'default': 'id_rsa'},
         'req_only_opt': {'requires_only': ['ssh-user']}
     }
     }, ['ssh-user'], ['ssh-key', 'host']]
])
def test_required_option_exception(monkeypatch,
                                   res_args,
                                   options,
                                   req_args,
                                   nonreq_args):
    mock_cmd_line_method(monkeypatch, res_args, options)
    with pytest.raises(exceptions.IRConfigurationException) as ex_info:
        spec.parse_args('test', {})

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

    [{'host': None,
      'command0': 'virsh',
      'from-file': {
          'virsh': {
              'host': 'earth',
          }
      },
      'ssh-user': None,
      'ssh-key': None},
     {'virsh': {
         'opt1': {'requires_only': ['host']},
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
      'ssh-user': 'id_rsa'}]
])
def test_required_options_are_set(monkeypatch,
                                  res_args,
                                  options,
                                  expected_args):
    mock_cmd_line_method(monkeypatch, res_args, options)
    actual_args = spec.parse_args('test', {})
    cmp(actual_args, expected_args)


def test_dynamic_topology(tmpdir):
    """
    Verifies the topology is dynamically constructed.
    """
    root_dir = tmpdir.mkdir("topology")
    controller_yml = root_dir.join("controller.yml")
    compute_yml = root_dir.join("compute.yml")
    ceph_yml = root_dir.join("ceph.yml")
    controller_yml.write("""---
memory: 8192
os: linux
name: controller
""")
    compute_yml.write("""---
memory: 1024
os: rhel
name: compute
""")
    ceph_yml.write("""---
memory: 2048
os: fedora
name: ceph
""")
    # prepare config
    config = ConfigParser.ConfigParser()
    config.add_section('defaults')
    config.set('defaults', 'topology', root_dir.strpath)
    res_args = dict(topology="10_controllers,2_compute")

    # process topology
    spec._post_process_command_args(res_args, config)
    topology = res_args['topology']
    assert 'controller' in topology
    assert 'compute' in topology
    assert 'ceph' not in topology
    assert topology['controller']['amount'] == 10
    assert topology['compute']['amount'] == 2
    assert topology['controller']['memory'] == 8192
    assert topology['compute']['memory'] == 1024
