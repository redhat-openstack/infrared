#!/usr/bin/python

from ansible.module_utils import fos
from ansible.module_utils.basic import AnsibleModule
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: fos_server_info
short_description: Retrieve information about one or more compute instances
description:
    - Retrieve information about server instances from OpenStack.
    - os_servers_facts module changing the openstack_servers facts
notes:
    - The result contains a list of servers.
requirements:
    - "python >= 2.7"
options:
   server:
     description:
       - restrict results to servers with names or UUID matching
         this glob expression (e.g., <web*>).
   detailed:
     description:
        - when true, return additional detail about servers at the expense
          of additional API calls.
     type: bool
     default: 'no'
   filters:
     description:
        - restrict results to servers matching a dictionary of
          filters
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
   all_projects:
     description:
       - Whether to list servers from all projects or just the current auth
         scoped project.
     type: bool
     default: 'no'
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather information about all servers named <web*> that are in an active state:
- fos_server_info:
    cloud: rax-dfw
    server: web*
    filters:
      vm_state: active
  register: result
- debug:
    msg: "{{ result.openstack_servers }}"
'''


def is_facts_module(module):
    return '_facts' in module._name


def module_main(module, result):
    params = module.params
    os_client = fos.ClientContext(params)
    openstack_servers = os_client.compute_server_search(
        server=None if 'server' not in params else params['server'],
        detailed=params['detailed'],
        filters=params['filters'],
        all_projects=params['all_projects'])
    if is_facts_module(module):
        result['ansible_facts'] = dict(
            openstack_servers=openstack_servers)
    else:
        result["openstack_servers"] = openstack_servers


def main():
    # define available arguments/parameters a user can pass to the module
    module_args = fos.openstack_full_argument_spec(
        server=dict(required=False),
        detailed=dict(required=False, type='bool', default=False),
        filters=dict(required=False, type='dict', default=None),
        all_projects=dict(required=False, type='bool', default=False),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # module.check_mode
    # This module allways in check mode, since it does not expected to change
    # state.

    try:
        module_main(module, result)
    except Exception as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
