import pytest
from cli import exceptions
from cli import spec


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
     {
         'host': {'help': 'help', 'required': True},
         'ssh-user': {'help': 'help2', 'required': True},
         'ssh-key': {'help': 'help3', 'default': 'id_rsa'}
     }, ['ssh-user'], ['host', 'ssh-key']],

    # data set #2
    [{'host': None,
      'command0': 'virsh',
      'ssh-user': None},
     {
         'host': {'help': 'help', 'required': True},
         'ssh-user': {'help': 'help2', 'required': True},
         'ssh-key': {'help': 'help3', 'default': 'id_rsa'}
     }, ['host', 'ssh-user'], ['ssh-key']],

    # data set #3 (require_only)
    [{'host': None,
      'command0': 'virsh',
      'ssh-user': None,
      'req_only_opt': True},
     {
         'host': {'help': 'help', 'required': True},
         'ssh-user': {'help': 'help2', 'required': True},
         'ssh-key': {'help': 'help3', 'default': 'id_rsa'},
         'req_only_opt': {'requires_only': ['ssh-user']}
     }, ['ssh-user'], ['ssh-key', 'host']]
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
def test_required_options_are_set(res_args,
                                  options,
                                  expected_args):
    actual_args = spec.override_default_values(res_args, options)
    cmp(actual_args, expected_args)
