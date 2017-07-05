#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2015, Tal Kammer <tkammer@redhat.com>
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

import requests
import os


DOCUMENTATION = '''
---
module: foreman_provisioner
version_added: "0.1"
short_description: Provision servers via Foreman
description:
   - Provision servers via Foreman
options:
   username:
     description:
         - login username to authenticate to Foreman
     required: true
     default: admin
   password:
     description:
         - Password of login user
     required: true
   auth_url:
     description:
         - The Foreman api url
     required: true
   host_id:
     description:
         - Name or ID of the host as listed in foreman
     required: true
   rebuild:
     description:
         - Should we rebuilt the requested host
     default: true
     required: false
   mgmt_strategy:
     description:
         - Whether to use Foreman or system ipmi command.
     default: 'foreman'
     required: false
   mgmt_action:
     description:
         - Which command to send with the power-management selected by
         mgmt_strategy. For example: reset, reboot, cycle
     default: 'cycle'
     required: false
   ipmi_username:
     description:
         - Host IPMI username
     default: 'ADMIN'
     required: false
   ipmi_password:
     description:
         - Host IPMI password
     default: 'ADMIN'
     required: false
   wait_for_host:
     description:
         - Number of seconds we should wait for the host given the 'rebuild' state was set.
     default: 10
     required: false
'''


MIN_SUPPORTED_VERSION = 2
MGMT_SUPPORTED_STRATEGIES = ['foreman', 'ipmi']


class ForemanManager(object):
    """
    This class represents a simple interface for foreman* to easily rebuild /
    get / reserve hosts from foreman.
    *Foreman: http://theforeman.org/
    """
    def __init__(self, url, username, password, extra_headers=None, version=2):
        """
        :param url: the url of the foreman we wish to authenticate with
        :param username: the username we will use to login
        :param password: the password we will use to login
        :param extra_headers: if we require extra headers to be added to the
        http request
        :param version: the version of foreman API we wish to use (default: 2)
        :type version: int
        """
        if version < MIN_SUPPORTED_VERSION:
            raise Exception("API version: {0} "
                            "is not supported at the moment".format(version))

        self.session = requests.Session()
        self.session.auth = (username, password)

        headers = {'Accept': 'application/json',
                   'Content-type': 'application/json'}

        if extra_headers:
            headers.update(extra_headers)

        self.session.headers.update(headers)

        self.url = url.rstrip('/')
        self.default_uri = '/api/v2/hosts/'

    def reserve_host(self, host_id):
        """
        This method 'tags' a host as reserved in foreman
        :param host_id: the name of ID of the host we wish to reserve
        :returns: the host information on success, else empty body
        :rtype: list of dictionaries -- [{"host": {}}]
        """
        #TODO(tkammer): add the option to provide the query itself after "?"
        request_url = '{0}/api/hosts_reserve' \
                      '?query=name ~ {1}'.format(self.url, host_id)
        response = self.session.get(request_url, verify=False)
        body = response.json()
        return body

    def release_host(self, host_id):
        """
        This method removed the 'tag' made by 'reserve_host" in foreman
        :param host_id: the name or ID of the host we wish to release
        :returns: the host name
        :rtype: list of strings
        """
        request_url = '{0}/api/hosts_release' \
                      '?query=name ~ {1}'.format(self.url, host_id)
        response = self.session.get(request_url, verify=False)
        body = response.json()
        Exception(body)
        return body

    def get_host(self, host_id):
        """
        This method returns the host details as listed in the foreman
        :param host_id: the name or ID of the host we wish to get
        :returns: host information
        :rtype: dict
        """
        request_url = '{0}/{1}/{2}'.format(self.url, self.default_uri, host_id)
        response = self.session.get(request_url, verify=False)
        body = response.json()
        return body

    def update_host(self, host_id, update_info):
        """
        This method updates a host details in foreman
        :param host_id: the name or ID of the host we wish to update
        :param update_info: params we wish to update on foreman
        :type update_info: dict
        :returns: host information
        :rtype: dict
        """
        request_url = '{0}/{1}/{2}'.format(self.url, self.default_uri, host_id)
        response = self.session.put(request_url, data=update_info, verify=False)
        body = response.json()
        return body.get('host')

    def set_build_on_host(self, host_id, flag):
        """
        sets the 'build' flag of a host to a given :param flag:
        :param host_id: the id or name of the host as it is listed in foreman
        :param flag: a boolean value (true/false) to set the build flag with
        """
        host = self.update_host(host_id, json.dumps({'build': flag}))
        self.get_host(host_id)
        if self.get_host(host_id).get('build') != flag:
            raise Exception("Failed setting build on host {0}".format(host_id))

    def bmc(self, host_id, command):
        """
        execute a command through the BMC plugin (on/off/restart/shutdown/etc)
        :param host_id: the id or name of the host as it is listed in foreman
        :param command: the command to send through the BMC plugin, supported
        commands: 'status', 'on', 'off', 'cycle', 'reset', 'soft'
        """
        request_url = '{0}/{1}/{2}/power'.format(self.url, self.default_uri, host_id)
        command = json.dumps({'power_action': command})
        response = self.session.put(request_url, data=command, verify=False)
        #TODO(tkammer): add verification that the BMC command was issued

    def ipmi(self, host_id, command, username, password):
        """
        execute a command through the ipmitool
        :param host_id: the ipmi id of the host
        :param command: the command to send through the ipmitool
        :param username: host IPMI username
        :param password: host IPMI password
        commands: 'status', 'on', 'off', 'cycle', 'reset', 'soft' # TBD
        """
        command = "ipmitool -I lanplus -H {host_id} -U {username} -P " \
                  "{password} chassis power {cmd}".format(
            host_id=host_id, username=username, password=password, cmd=command)
        return_code = subprocess.call(command, shell=True)

        if return_code:
            raise Exception("Call to {0}, returned with {1}".format(command, return_code))

    def _validate_bmc(self, host_id):
        """
        This method validate that there is at least one BMC on the given host
        :param host_id: the id or name of the host as it is listed in foreman
        """
        request_url = '{0}/{1}/{2}/interfaces'.format(
            self.url, self.default_uri, host_id)
        response = self.session.get(request_url, verify=False)
        body = response.json()
        missing_bmc = True
        for interface in body['results']:
            if "BMC" in interface['type'].upper():
                missing_bmc = False
                break
        return missing_bmc

    def provision(self, host_id, mgmt_strategy, mgmt_action,
                  ipmi_username, ipmi_password, wait_for_host=10):
        """
        This method rebuilds a machine, doing so by running get_host and bmc.
        :param host_id: the name or ID of the host we wish to rebuild
        :param mgmt_strategy: the way we wish to reboot the machine
        (i.e: foreman, ipmi, etc)
        :param mgmt_action: the action we wish to use with the strategy
        (e.g: cycle, reset, etc)
        :param wait_for_host: number of seconds the function waits after host
        finished rebuilding before checking connectivity
        :param ipmi_username: remote server username (IPMI)
        :param ipmi_password: remote server password (IPMI)
        :raises: KeyError if BMC hasn't been found on the given host
                 Exception in case of machine could not be reached after
                 rebuild
        """
        wait_for_host = int(wait_for_host)
        if self._validate_bmc(host_id):
            raise KeyError("BMC not found on {}".format(host_id))
        building_host = self.get_host(host_id)
        self.set_build_on_host(host_id, True)
        if mgmt_strategy == 'foreman':
            self.bmc(host_id, mgmt_action)
        elif mgmt_strategy == 'ipmi':
            host = "{0}.{1}".format(building_host.get('interfaces')[0].get('name'), building_host.get('domain_name'))
            self.ipmi(host, mgmt_action, ipmi_username, ipmi_password)
        else:
            raise Exception("{0} is not a supported "
                            "management strategy".format(mgmt_strategy))
        if wait_for_host:
            while self.get_host(host_id).get('build'):
                time.sleep(wait_for_host)

            command = "ping -q -c 30 -w 300 {0}".format(building_host.get('name'))
            return_code = subprocess.call(command, shell=True)

            if return_code:
                raise Exception("Could not reach {0}, rc={1}, cmd={2}".format(host_id, return_code, command))

def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(default='admin'),
            password=dict(required=True),
            auth_url=dict(required=True),
            host_id=dict(required=True),
            rebuild=dict(default=True, type='bool', choices=BOOLEANS),
            mgmt_strategy=dict(default='foreman',
                               choices=MGMT_SUPPORTED_STRATEGIES),
            mgmt_action=dict(default='cycle', choices=['on', 'off', 'cycle',
                                                       'reset', 'soft']),
            wait_for_host=dict(default=10),
            ipmi_username=dict(default='ADMIN'),
            ipmi_password=dict(default='ADMIN')))

    foreman_client = ForemanManager(url=module.params['auth_url'],
                                    username=module.params['username'],
                                    password=module.params['password'])

    status_changed = False

    if module.boolean(module.params['rebuild']):
        try:
            foreman_client.provision(module.params['host_id'],
                                     module.params['mgmt_strategy'],
                                     module.params['mgmt_action'],
                                     module.params['ipmi_username'],
                                     module.params['ipmi_password'],
                                     module.params['wait_for_host'])
        except KeyError as e:
            module.fail_json(msg=e.message)
        else:
            status_changed = True

    #TODO(tkammer): implement RESERVE and RELEASE
    host = foreman_client.get_host(module.params['host_id'])
    interface = foreman_client.get_host('{0}/interfaces'.format(module.params['host_id']))
    if host.has_key('error'):
        module.fail_json(msg=host['error'])

    module.exit_json(changed=status_changed, host=host, interface=interface)


from ansible.module_utils.basic import *
main()
