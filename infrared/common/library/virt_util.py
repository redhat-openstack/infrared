#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) 2017, Red Hat, Inc.
# Written by Oleh Anufriiev <oanufrii@redhat.com>
#
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
from collections import defaultdict
import ipaddress
from xml.etree import cElementTree as ET

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception


try:
    from collections.abc import Mapping as collections_Mapping
except ImportError:
    from collections import Mapping as collections_Mapping

try:
    import libvirt
except ImportError:
    HAS_VIRT = False
else:
    HAS_VIRT = True

DOCUMENTATION = '''
---
module: virt_util
short_description: InfraRed libvirt helpers
description:
    - Difficult to implement in Ansible and/or reusable libvirt related steps
options:
  domain:
    description:
      - Libvirt domain name
    type: 'str'
  network:
    description:
      - Libvirt network name
    type: 'str'
  device_class:
    description:
      - Any entity inside <devices></devices> tags in domain definition XML
      - (interface, disk, controller, video etc.)
    type: 'str'
  hosts:
    description:
      - List of inventory host names
    type: 'list'
  command:
    description:
      - Module command
    choices: ["static_dhcp4", "instack_info", "domains_and_networks", "domain_xml2dict",
              "domain_xml_devices", "net_xml2dict"]
requirements:
    - "python >= 2.6"
    - "libvirt-python"
notes:
    - To extend this module just implement additional Util class method,
      decorated with @command(command_name, **command_args) decorator.
      Command args are Ansible module argument_spec declarations
      (Module testing http://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html)
'''


EXAMPLE = '''
- name: Staticaly assign IPv4 address to domain from network dhcp range and/or return assigned one
    virt_util:
        command: 'static_dhcp4'
        domain: 'undercloud-0'
        network: 'management'

- name: Get domain information for instackenv.json
    virt_util:
        command: 'instack_info'
        domain: 'undercloud-0'
        network: 'management'

- name: Get existing domains list and networks, these domains connected to (for cleanup)
    virt_util:
        command: 'domains_and_networks'
        hosts: "{{ groups['all'] }}"

- name: Get network libvirt definition XML as dict
    virt_util:
        command: 'net_xml2dict'
        network: 'management'

- name: Get domain libvirt definition XML as dict
    virt_util:
        command: 'domain_xml2dict'
        domain: 'controller-0'

- name: Get list of devices of specified class, configured in libvirt domain definition XML
    virt_util:
        command: 'domain_xml_devices'
        network: 'controller-0'
        device_class: 'disk'
'''


RETURN = '''
ipaddr:
  description:
      - IPv4 address, assigned to domain in network, specified by arguments
      - command == 'static_dhcp4'
  type: 'str'

networks:
  description:
      - virt_net module 'info' command result with 'dhcp_leases' section extended by static dhcp records
      - command == 'domains_and_networks'
  type: 'dict'
  sample: {'networks': {'networks': {'management': {...}, 'external': {...}}}}

domains:
  description:
      - Names of existing libvirt domains for list of namse, specified by hosts argument
      - command == 'domains_and_networks'
  type: 'dict'
  sample: {'list_vms': ['controller-0', 'undercloud-0']}

instack_info:
  description:a
      - Domain infrormation, prepared for instackenv.json
      - command == 'instack_info'
  type: 'dict'
  sample: "instack_info": {"arch": "x86_64", "cpu": "8", "disk_bytes": 42949672960, "disks": ['vda'], ...}

domain:
  description:
      - command == 'domain_xml2dixt'
  type: 'dict'
  sample: {'domain': ...}

devices:
  description:
      - command == 'deomain_xml_devices'
  type: 'dict'
  sample: {'devices': [{...}, {...}, ...]}

network:
  description:
      - command == 'net_xml2dict'
  type: 'dict'
  sample: {'network': ...}

'''


class UtilError(Exception):
    pass


COMMANDS = {}
ALL_ARGS = {'uri': {'type': 'str', 'default': 'qemu:///system'}}


class Util(object):
    module = {}

    def command(cmd_name, **kwargs):
        """Decorator for registering commands

           Register class method as module command
           :param cmd_name: module command name
           kwargs - method args definition in Ansible module args_spec format
        """
        def wrap(func):
            COMMANDS.setdefault(cmd_name, {'call': func,
                                           'args': kwargs.keys()})
            ALL_ARGS.update(kwargs)
            return func
        return wrap

    def _validate_args(self, *args):
        """Check if arguments, listed in 'args' are passed and have values.

           :return: dict {arg_name: arg_value}
        """
        absent = []
        result = {}
        for arg in args:
            val = self.module.params.get(arg, None)
            if val is None:
                absent.append(arg)
            else:
                result[arg] = val
        if absent:
            raise UtilError("Expected {} to be specified".format(absent))

        return result

    def __call__(self, module):
        """Call module command with arguments.

           * From 'module' object determines command.
           * From COMMANDS dict get the function object and required arguments
             names
           * Get arguments values
           * Run function object with arguments
        """
        self.module = module

        uri = list(self._validate_args('uri').values())[0]
        self.conn = libvirt.open(uri)
        if self.conn is None:
            raise UtilError('Failed to open connection to {}'.format(uri))

        command = list(self._validate_args('command').values())[0]

        kwargs = self._validate_args(*COMMANDS[command]['args'])
        return COMMANDS[command]['call'](self, **kwargs)

    @staticmethod
    def _xmlET2dict(t):
        """Convert XML Element tree to dict"""

        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(Util._xmlET2dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {t.tag: {
                k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
        if t.attrib:
            d[t.tag].update((k, v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[t.tag]['text'] = text
            else:
                d[t.tag] = text
        return d

    @staticmethod
    def _xml2dict(xml):
        """Convert XML string to dict"""

        return Util._xmlET2dict(ET.XML(xml))

    @staticmethod
    def _get_key_as_list(value):
        """Return a key of a dict as a list"""
        if not value:
            return []
        elif isinstance(value, collections_Mapping):
            return [value]
        else:
            return value

    @command('domain_xml2dict', domain={'type': 'str'})
    def get_dom_dict(self, domain=''):
        """Get domain xml from libvirt as dict"""

        dom = self.conn.lookupByName(domain)
        if dom is None:
            raise UtilError("Domain '{}' not found".format(domain))
        return self._xml2dict(dom.XMLDesc())

    @command('domain_xml_devices', domain={'type': 'str'},
             device_class={'type': 'str'})
    def get_dom_devices(self, domain='', device_class=''):
        """Get list of devices of specified class"""

        dom_dict = self.get_dom_dict(domain=domain)
        devices = dom_dict['domain']['devices'].get(device_class, [])
        if type(devices) is not list:
            devices = [devices]
        return {'devices': devices}

    @command('net_xml2dict', network={'type': 'str'})
    def get_net_dict(self, network=''):
        """Get network xml from libvirt as dict"""

        net = self.conn.networkLookupByName(network)
        if net is None:
            raise UtilError("Network '{}' not found".format(network))
        net_obj = Util._xml2dict(net.XMLDesc())
        return net_obj

    @command('static_dhcp4', domain={'type': 'str'},
             network={'type': 'str'})
    def static_dhcp_ip4(self, domain='', network=''):
        """Set static dhcp address for domain in network.

           * Get network dhcp; determine netmask and ip range (start, end)
           * Determine mac address of domain's interface, connected
             to network
           * Generate ip range list and exclude assignet addresses
           * Assign firsh available address to domain

           If address of network for domain is already assigned - return
           this address.
        """
        interfaces = self.get_dom_devices(domain=domain,
                                          device_class='interface')['devices']
        mac = ''
        for interface in interfaces:
            if interface['source'].get('network') == network:
                mac = interface['mac']['address']
                break
        else:
            raise UtilError("Domain '{}' is not  conneted to "
                            "network '{}'".format(domain, network))

        net = self.get_net_dict(network)

        ip = net['network']['ip']
        if type(ip) is not list:
            ip = [ip]

        for item in ip:
            if 'family' in item and item['family'] == 'ipv6':
                continue

            net_addr = net['network']['ip'].get('address')
            netmask = net['network']['ip'].get('netmask')

            network_addresses = [i for i in ipaddress.IPv4Network('{}/{}'.format(
                net_addr, netmask)).iterhosts()]
            network_addresses.remove(ipaddress.IPAddress(net_addr))

            dhcp = item.get('dhcp')
            if dhcp is not None:
                dhcp_range = dhcp.get('range')

                if dhcp_range:
                    start_ind = network_addresses.index(
                        ipaddress.IPAddress(dhcp_range['start']))
                    stop_ind = network_addresses.index(ipaddress.IPAddress(
                        dhcp_range['end']))
                    network_addresses = network_addresses[
                        start_ind:stop_ind + 1]

            assigned = dhcp.get('host', [])
            if type(assigned) is not list:
                assigned = [assigned]

            for record in assigned:
                network_addresses.remove(ipaddress.IPAddress(record['ip']))
                if record['mac'] == mac:
                    return {'ipaddr': record['ip']}

            if not network_addresses:
                raise UtilError("No free dhcp range addresses "
                                "left for network '{}'".format(network))

            lvnet = self.conn.networkLookupByName(network)
            lvnet.update(libvirt.VIR_NETWORK_UPDATE_COMMAND_ADD_LAST,
                         libvirt.VIR_NETWORK_SECTION_IP_DHCP_HOST, 0,
                         "<host mac='{}' name='{}' ip='{}'/>".format(
                             mac, domain, network_addresses[0]))

            return {'changed': True, 'ipaddr': network_addresses[0]}

    @command('instack_info', domain={'type': 'str'},
             network={'type': 'str'})
    def get_dom_info(self, domain='', network=''):
        """Gather domain information for instackenv"""

        dom_obj = self.get_dom_dict(domain=domain)
        dom = self.conn.lookupByName(domain)
        result = {}
        result['name'] = dom_obj['domain']['name']

        # TODO(oanufrii): implement conversion in case of enother unit
        result['memory_kibs'] = dom_obj['domain']['memory']['text']
        result['cpu'] = dom_obj['domain']['vcpu']['text']
        result['arch'] = dom_obj['domain']['os']['type']['arch']
        disks = []
        disks_obj = self.get_dom_devices(domain=domain,
                                         device_class='disk')['devices']
        for disk in disks_obj:
            if disk['device'] == 'disk':
                disks.append(disk['target']['dev'])
            if disk['alias']['name'] == 'virtio-disk0':
                result['disk_bytes'] = int(dom.blockInfo(
                    disk['target']['dev'])[0])
        result['disks'] = disks

        net = self.get_net_dict(network)
        hosts = self._get_key_as_list(net['network']['ip']['dhcp']['host'])
        for host in hosts:
            if host['name'] == domain:
                result['mac'] = host['mac']

        return {'instack_info': result}

    @command('domains_and_networks', hosts={'type': 'list'})
    def get_domains_and_networks(self, hosts=''):
        """Get domains and networks for cleanup.

           * Accepts list of inventory hosts (all)
           * Determine which of hosts are defined VMs
           * Determine networks list, this domains are connected
           * Get networks dhcp info: leases and static dhcp

           Return: list_vms: list of existing domains names
                   networks: {
                                 name: {
                                     dhcp_leases: [
                                        {hostname: ..., ipaddr: ...}
                                     ]
                                }
                             }
        """
        domains = set()
        networks = {}
        for name in hosts:
            try:
                dom_ifaces = self.get_dom_devices(
                    domain=name, device_class='interface')['devices']
            except Exception:
                continue
            domains.add(name)
            for interface in dom_ifaces:
                net_name = interface['source'].get('network')
                if net_name is not None and net_name not in networks:
                    virt_net = self.conn.networkLookupByName(net_name)
                    dhcp_leases = virt_net.DHCPLeases()
                    net_dict = self.get_net_dict(net_name)
                    ip = net_dict['network']['ip']
                    if type(ip) is not list:
                        ip = [ip]
                    for family in ip:
                        dhcp = family.get('dhcp')
                        if dhcp is None:
                            continue
                        hosts = self._get_key_as_list(dhcp.get('host'))
                        for record in hosts:
                            dhcp_leases.append({'hostname': record['name'],
                                                'ipaddr': record['ip']})
                    networks[net_name] = {'dhcp_leases': dhcp_leases}

        return {'domains': {'list_vms': list(domains)},
                'networks': {'networks': networks}}


def main():
    u = Util()
    args_spec = ALL_ARGS.copy()
    args_spec['command'] = dict(choices=COMMANDS.keys())
    module = AnsibleModule(argument_spec=args_spec)

    if not HAS_VIRT:
        module.fail_json(
            msg='The `libvirt` module is not importable. '
            'Check the requirements.')

    try:
        result = u(module)
        module.exit_json(**result)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
