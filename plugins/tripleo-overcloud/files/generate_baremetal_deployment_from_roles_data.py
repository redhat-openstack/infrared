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


def parse_networks_names(networks_data: List[Dict]) -> Dict:
    parsed_names = {}
    for network in networks_data:
        name = network.get('name')
        name_lower = network.get('name_lower')
        if not name or not name_lower:
            # no name, no mapping; no lower_name, use the default rules
            continue
        parsed_names[name] = name_lower
    return parsed_names


class BaremetalRoleData():

    @property
    def generic_type(self) -> str:
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
        """An opionionated but sane default profile."""
        if self.generic_type == 'controller':
            return 'control'
        return self.generic_type

    def _parse_networks(self, networks: List, networks_data: Dict) -> Dict:

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
        if 'compute' in self._tags and self._dvr_network:
            parsed_nets[self._dvr_network] = {}
        for net in networks:
            try:
                net_name = networks_data[net]
            except KeyError:
                # the default is lowercase
                net_name = net.lower()
            parsed_nets[net_name] = {}
        return parsed_nets

    def __init__(self, role_data: Dict, networks_data: Dict,
                 enable_profiles: bool = False,
                 dvr_network: str = 'external') -> None:
        self.name = role_data.get('name')
        self.roles_count = role_data.get('CountDefault', 0)
        self._hostname_format = role_data.get('HostnameFormatDefault')
        self._default_network = role_data.get('default_route_networks', [])
        self._tags = role_data.get('tags', [])
        self._dvr_network = dvr_network
        self._networks = self._parse_networks(role_data.get('networks', {}),
                                              networks_data)
        self._enable_profiles = enable_profiles

    def to_baremetal_format(self, network_templates_dir: Path):
        out = {}
        out['name'] = self.name
        out['count'] = self.roles_count
        if self._hostname_format:
            out['hostname_format'] = self._hostname_format
        defaults = {}
        if self._enable_profiles:
            defaults['profile'] = self.profile

        network_config = {}
        if self._default_network:
            network_config['default_route_network'] = self._default_network
        if network_templates_dir:
            candidate_net_template = Path(network_templates_dir,
                                          '{}.j2'.format(self.generic_type))
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


def convert_role_data(roles_data: Dict, networks_data: Dict,
                      network_templates_dir: Path,
                      roles_count: Dict,
                      enable_profiles: bool = False,
                      dvr_network: str = 'external') -> None:

    all_roles = []
    for role_data in roles_data:
        role_obj = BaremetalRoleData(role_data, networks_data, enable_profiles,
                                     dvr_network)
        nc = 0
        try:
            nc = int(roles_count.get(role_obj.name))
        except (TypeError, ValueError):
            # either not available, or not an integer, we can accept 0
            # and add the role to the list, so that
            # the validation does not fail.
            pass
        role_obj.roles_count = nc
        all_roles.append(role_obj.to_baremetal_format(network_templates_dir))
    print(yaml.dump(all_roles, sort_keys=False))


def parse_opts(argv):
    parser = argparse.ArgumentParser(
            description='Convert to Ansible Jinja2 NIC config templates.')
    parser.add_argument('roles_data',
                        metavar='ROLES_DATA',
                        help='Path of the roles_data.yaml file',
                        default='roles_data.yaml')
    parser.add_argument('-n', '--networks-file',
                        metavar='NETWORK_FILES',
                        help='Path of the file with network definitions')
    parser.add_argument('-t', '--network-templates',
                        metavar='NETWORK_TEMPLATES',
                        help='Directory of the network templates')
    parser.add_argument('-c', '--roles-count',
                        metavar=('ROLE_TYPE', 'COUNT'),
                        nargs=2, action='append', default=[],
                        help='Override the count of nodes for each node type')
    parser.add_argument('-p', '--enable-profiles', action='store_true',
                        help='Whether add some default profiles to the nodes')
    parser.add_argument('-d', '--dvr-external-network', nargs='?',
                        const='external', type=str,
                        help='Name of external network when using DVR')
    # FIXME: add parameter to set the firstboot options
    opts = parser.parse_args(argv[1:])
    return opts


def main():
    opts = parse_opts(sys.argv)

    roles_count = dict(opts.roles_count)

    with open(opts.roles_data, 'r') as rdf:
        roles_data = yaml.safe_load(rdf)
    # get the names of the networks
    networks_data = {}
    if opts.networks_file:
        with open(opts.networks_file, 'r') as ndf:
            networks_data_file = yaml.safe_load(ndf)
        networks_data = parse_networks_names(networks_data_file)
    convert_role_data(roles_data, networks_data, opts.network_templates,
                      roles_count, opts.enable_profiles,
                      opts.dvr_external_network)


if __name__ == '__main__':
    main()
