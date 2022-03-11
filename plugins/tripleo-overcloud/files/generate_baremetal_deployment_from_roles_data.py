#!/usr/bin/env python3
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
from pathlib import Path
import re
import sys
from typing import Dict, List

import yaml


class BaremetalRoleData():

    @property
    def type(self) -> str:
        # by default the "expanded" name,
        # but if a special tag is available use it
        # special cases
        for special_case in ['controller', 'compute']:
            if special_case in self._tags:
                return special_case
        if 'ceph' in self._tags and 'storage' in self._tags:
            return 'ceph-storage'
        return self.name.lower()

    @property
    def profile(self) -> str:
        if self.type == 'controller':
            return 'control'
        return self.type

    @classmethod
    def _parse_networks(cls, networks: List) -> Dict:

        def _expanded_id(name: str, sep: str = '_') -> str:
            """Transform a 'ObjectSpecialName' identifier into
            its expanded form object_special_name which is the format
            used by baremetal network definitions mostly everywhere."""
            return sep.join([el.lower()
                             for el in re.split(r'([A-Z]+[^A-Z]*)', name)
                             if el])

        # parsed_nets = OrderedDict()
        parsed_nets = {}
        parsed_nets['ctlplane'] = {'vif': True}
        for net in networks:
            net_name = _expanded_id(net)
            parsed_nets[net_name] = {}
        return parsed_nets

    def __init__(self, role_data: Dict) -> None:
        self.name = role_data.get('name')
        self.node_count = role_data.get('CountDefault', 0)
        self._hostname_format = role_data.get('HostnameFormatDefault')
        self._default_network = role_data.get('default_route_networks', [])
        self._networks = self._parse_networks(role_data.get('networks', {}))
        self._tags = role_data.get('tags', [])

    def to_baremetal_format(self, network_templates_dir: Path):
        out = {}
        out['name'] = self.name
        out['count'] = self.node_count
        if self._hostname_format:
            out['hostname_format'] = self._hostname_format
        defaults = {}
        defaults['profile'] = self.profile

        network_config = {}
        if self._default_network:
            network_config['default_route_network'] = self._default_network
        if network_templates_dir:
            candidate_net_template = Path(network_templates_dir,
                                          '{}.j2'.format(self.type))
            if candidate_net_template.is_file():
                network_config['template'] = str(
                    candidate_net_template.resolve())
        if network_config:
            defaults['network_config'] = network_config

        networks = []
        for net_name, net_data in self._networks.items():
            net_item = {'network': net_name}
            net_item.update(net_data)
            networks.append(net_item)
        if networks:
            defaults['networks'] = networks

        if defaults:
            out['defaults'] = defaults
        return out


def convert_role_data(roles_data: Dict, network_templates_dir: Path,
                      node_count: Dict) -> None:
    all_roles = []
    for role_data in roles_data:
        role_obj = BaremetalRoleData(role_data)
        nc = None
        try:
            nc = int(node_count.get(role_obj.type))
        except TypeError:
            # trying to convert None -> not found, use a default
            # at least one node
            nc = 1
        except ValueError:
            # value set but not an integer
            nc = None
        try:
            # try a more specific match
            nc = int(node_count.get(role_obj.name.lower()))
        except (TypeError, ValueError):
            # keep the previous value
            pass
        if nc is not None:
            role_obj.node_count = nc
        if role_obj.node_count > 0:
            all_roles.append(
                role_obj.to_baremetal_format(network_templates_dir))
    print(yaml.dump(all_roles, sort_keys=False))


def parse_opts(argv):
    parser = argparse.ArgumentParser(
            description='Convert to Ansible Jinja2 NIC config templates.')
    parser.add_argument('roles_data',
                        metavar='ROLES_DATA',
                        help='Path of the roles_data.yaml file',
                        default='roles_data.yaml')
    parser.add_argument('-n', '--network-templates',
                        metavar='NETWORK_TEMPLATES',
                        help='Directory of the network templates')
    parser.add_argument('-c', '--node-count',
                        metavar=('NODE_TYPE', 'COUNT'),
                        nargs=2, action='append', default=[],
                        help='Override the mount of nodes for each node type')
    # FIXME: add parameter to set the firstboot options
    opts = parser.parse_args(argv[1:])
    return opts


def main():
    opts = parse_opts(sys.argv)

    node_count = dict(opts.node_count)

    with open(opts.roles_data, 'r') as rdf:
        roles_data = yaml.safe_load(rdf)
    convert_role_data(roles_data, opts.network_templates, node_count)


if __name__ == '__main__':
    main()
