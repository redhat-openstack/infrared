#!/usr/bin/python

# Copyright: (c) 2022, Red Hat, Inc.
# Written by Luigi Toscano <ltoscano@redhat.com>

# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from collections import Counter
import re

from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = r'''
---
module: node_data_roles

short_description: Compute the node count for each role

version_added: "1.0.0"

description: Return the amount of nodes for each role.

options:
    tht_roles:
        description: A comma-separated list of role names.
        required: true
        type: str
    overcloud_nodes:
        description: The overcloud nodes.
        required: true
        type: list

author:
    - Luigi Toscano
'''


EXAMPLES = r'''
- name: Count the nodes
  roles_node_count:
    tht_roles: 'ControllerStorageNfs,CephStorage,Compute'
    overcloud_nodes:
      - controller-1
      - controller-2
      - controller-3
      - compute-1
      - compute-2
      - ceph-1
      - ceph-2
      - ceph-3
      - networker-1
'''

RETURN = r'''
nodes_count:
    description: |
      The dictionary containing information about the amount of nodes
      for each role
    type: dict
    returned: always
    sample: {
        'CephStorage': 3,
        'Compute': 2,
        'ControllerStorageNfs': 3
    }
'''

ROLE_NAMES_MAPPING = {
    'ceph': 'CephStorage',
    'swift': 'ObjectStorage',
    'compute_dvr': 'ComputeDVR',
    'aio': 'Standalone',
    'computehci': 'ComputeHCI',
}


THT_ROLES_MAPPING = dict([
    ('^(Controller).*',
        {'node_name': 'controller'}),
    ('^(Novacontrol).*',
        {'node_name': 'novacontrol'}),
    ('^(Compute)(?!HCI).*$',
        {'node_name': 'compute'}),
    ('^(Ceph).*',
        {'node_name': 'ceph'}),
    ('^(ObjectStorage).*',
        {'node_name': 'swift'}),
    ('^(Database).*',
        {'node_name': 'database'}),
    ('^(Messaging).*',
        {'node_name': 'messaging'}),
    ('^(Networker).*',
        {'node_name': 'networker'}),
    ('^(HciCephAll).*',
        {'node_name': 'hcicephall'}),
    ('^(ComputeHCI).*',
        {'node_name': 'computehci'}),
])


def _get_tht_node_name(tht_role):
    found_node = None
    for tht_roles_regex in THT_ROLES_MAPPING.keys():
        if re.match(tht_roles_regex, tht_role):
            found_node = THT_ROLES_MAPPING[tht_roles_regex]['node_name']
            break
    return found_node


def main():
    module_args = dict(
        tht_roles=dict(type='str', required=True),
        overcloud_nodes=dict(type='list', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    result = dict(
        changed=False,
        nodes_count={},
    )

    if module.check_mode or not module.params['tht_roles']:
        module.exit_json(**result)

    overcloud_node_counter = Counter(
        [host_name.rstrip('1234567890-').split('-')[-1]
         for host_name in module.params['overcloud_nodes']]
    )
    tht_roles = module.params['tht_roles'].split(',')

    if len(tht_roles) == 1:
        # just one element: it is a role profile in IR or autodetect
        # for each overcloud name, find out the role
        for oc_name, oc_count in overcloud_node_counter.items():
            oc_role_name = ROLE_NAMES_MAPPING.get(oc_name,
                                                  oc_name.capitalize())
            result['nodes_count'][oc_role_name] = oc_count
    else:
        # list of roles, for each of them find out which overcloud nodes
        # are associated to them, and count them.
        for tht_role in tht_roles:
            found_node_name = _get_tht_node_name(tht_role)
            if found_node_name:
                found_node_count = overcloud_node_counter.get(found_node_name,
                                                              0)
                result['nodes_count'][tht_role] = found_node_count

    module.exit_json(**result)


if __name__ == '__main__':
    main()
