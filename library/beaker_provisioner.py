#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2016, Ariel Opincaru <aopincar@redhat.com>
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


import json
import time
import subprocess
from urlparse import urljoin
from xml.dom import minidom

import requests
import requests.auth

DOCUMENTATION = '''
---
module: beaker_provisioner
version_added: "0.1"
short_description: Provision servers via Beaker
description:
   - Provision servers via Beaker
options:
    server_url:
        description:
            - Base URL of Beaker server
        required: tru
    username:
        description:
            - Login username to authenticate to Beaker
        required: false
        default: admin
    password:
        description:
            - Password of login user
            required: true
    fqdn:
        description:
            - Fully qualified domain name of a system
        required: true
    action:
        description:
            - Action to perform
        required: true
        choices: 'provision', 'release'
    distro_tree_id:
        description:
            - Distro Tree ID
        default: 71576
        required: false
'''

LOAN_COMMENT = 'Loaned by BeakerManager'
SYS_FQDN_PATH = '/systems/{fqdn}/'
WAIT_BETWEEN_PROVISION_CHECKS = 10


def is_fail(status_code, success_code=200):
    """
    Check if a command execution failed or not

    :param status_code: The command status code
    :param success_code: Success code (default is 200)
    :return: False if status code is equal to success code, otherwise, False
    """

    return status_code != success_code


class BeakerManager(object):
    REQ_URL = dict(
        ALL='',
        FREE='free/',
        LOAN='loans/',
        VIEW='view/',
        RETURN='loans/+current',
        RESERVE='reservations/',
        RELEASE='reservations/+current',
        PROVISION='installations/'
    )

    def __init__(self, url, username, password, fqdn,
                 verify=False, disable_warnings=True):
        """
        BeakerManager initializer.

        :param url: Base URL of the Beaker server
        :param username: Authentication username
        :param password: Authentication password
        :param fqdn: Fully qualified domain name of a system
        :param verify: Whether to Check SSL certificate or not (Can specify a
        path to a certificates file. Default = False)
        :param disable_warnings: Hide unverified HTTPS requests warnings (
               default = False)
        """

        self.base_url = url
        self.auth = requests.auth.HTTPBasicAuth(username, password)
        self.fqdn = fqdn
        self.changed = False

        self.session = requests.Session()
        self.session.auth = self.auth

        # verify the SSL certificate or not (and disable warning if needed)
        self.session.verify = verify
        if disable_warnings:
            requests.packages.urllib3.disable_warnings()

        # cookie workaround - consider changing with _get_last_activity()
        self.get(limit=1)

    def view(self):
        headers = {'Content-Type': 'application/json'}
        old_params, new_params = self.session.params, {'tg_format': 'turtle'}
        url = self.base_url + '/view/' + self.fqdn
        self.session.params = new_params
        resp = self.session.get(url, headers=headers)
        self.session.params = old_params

        return is_fail(resp.status_code)

    def view2(self):
        headers = {'Content-Type': 'application/json'}
        url = self.base_url + '/systems/' + self.fqdn + '/'
        resp = self.session.get(url, headers=headers)
        print resp.status_code
        print resp.url
        print resp.content

        return is_fail(resp.status_code)

    # TODO: Adds FQDN existence check in __init__()
    def get(self, limit=0, filters=None, req='FREE'):
        """
        Get a list of free systems

        :param limit: Limit the number of free systems to return (0 = no limit)
        :param filters: A dictionary for system filtering
        :param req: A String representing the wanted request (Default = 'FREE')
        :return: List of free systems
        """

        if filters is None:
            filters = {}
        url = self._build_url(req)
        params = dict(
            tg_format='atom',
            list_tgp_limit=limit
        )

        cnt = 0
        for f_name, f_val in filters.iteritems():
            params['systemsearch-{0}.table'.format(cnt)] = f_name
            params['systemsearch-{0}.operation'.format(cnt)] = 'is'
            params['systemsearch-{0}.value'.format(cnt)] = f_val
            cnt += 1

        # save the session params before changes
        saved_params = self.session.params

        self.session.params = params
        resp = self.session.get(url)

        # restore session params
        self.session.params = saved_params

        parsed_xml = minidom.parseString(resp.content)
        feed = parsed_xml.getElementsByTagName('feed')[0]
        entries = feed.getElementsByTagName('entry')

        systems = set()
        for entry in entries:
            systems.add(entry.getElementsByTagName('title')[0].firstChild.data)

        systems = list(systems)
        systems.sort()
        return systems

    def release(self):
        """
        Release the system

        :return: List of systems which have not released
        """

        return self._release_system() or self._return_system()

    def reserve(self):
        """
        Reserve the system

        :return: List of reserved systems
        """

        failed = False

        if self._loan_system():
            failed = True
        if not failed and self._reserve_system():
            self._return_system()
            failed = True

        return failed

    def _loan_system(self):
        """
        Loan a system

        :return: False for success, otherwise, True
        """

        headers = {'Content-Type': 'application/json'}
        url = self._build_url('LOAN', self.fqdn)
        resp = self.session.post(url, headers=headers,
                                 data=json.dumps({'comment': LOAN_COMMENT}))

        return is_fail(resp.status_code)

    def _return_system(self):
        """
        Return a loaned system

        :return: False for success, otherwise, True
        """

        headers = {'Content-Type': 'application/json'}
        url = self._build_url('RETURN', self.fqdn)
        resp = self.session.patch(url, headers=headers,
                                  data=json.dumps({'finish': 'now'}))

        return is_fail(resp.status_code)

    def _reserve_system(self):
        """
        Reserve a system

        :return: False for success, otherwise, True
        """

        headers = {'Content-Type': 'application/json'}
        url = self._build_url('RESERVE', self.fqdn)
        resp = self.session.post(url, headers=headers)

        return is_fail(resp.status_code)

    def _release_system(self):
        """
        Release a reserved system

        :return: False for success, otherwise, True
        """

        headers = {'Content-Type': 'application/json'}
        url = self._build_url('RELEASE', self.fqdn)
        resp = self.session.patch(url, headers=headers,
                                  data=json.dumps({'finish_time': 'now'}))

        return is_fail(resp.status_code)

    def provision(self, distro_id, ks_meta=None, koptions=None,
                  koptions_post=None, reboot=False, wait_for_host=True,
                  provision_timeout=1200):
        """
        Provision a system

        :param distro_id: an ID identifying the distro tree to be provisioned
        :param ks_meta: Kickstart metadata variables (string)
        :param koptions: Kernel options to be passed to the installer (string)
        :param koptions_post: Kernel options to be configured after
               installation (string)
        :param reboot: If true, the system will be rebooted immediately after
               the installer netboot configuration has been set up (boolean)
        :param wait_for_host: Whether or not wait for host to finish
        provisioning
        :param provision_timeout: Max time to wait for provisioning process
        (wait_for_ssh) to be done
        :return: False for success, otherwise, True
        """

        if wait_for_host:
            last_pre_provison_activity = self._get_last_system_activity()

        headers = {'Content-Type': 'application/json'}
        url = self._build_url('PROVISION', self.fqdn)
        params = json.dumps({
            'distro_tree': {'id': str(distro_id)},
            'ks_meta': str(ks_meta),
            'koptions': str(koptions),
            'koptions_post': str(koptions_post),
            'reboot': str(reboot)
        })

        resp = self.session.post(url, data=params, headers=headers)

        if is_fail(resp.status_code, 201):
            return True

        if wait_for_host and self._provision_waiter(
                last_pre_provison_activity, provision_timeout):
            return True

        return False

    def _get_last_system_activity(self):
        """
        Return the ID of the last system's activity
        """

        headers = {'accept': 'application/json'}
        url = self.base_url + '/activity/system'
        self.session.params = {'q': 'system:' + self.fqdn}
        resp = self.session.get(url, headers=headers)

        return json.loads(resp.text)['entries'][0]

    def _provision_waiter(self, pre_provision_activity_id, timeout):
        """
        Waiting until the provisioning process id done and the system responses
        tp ping requests

        :param pre_provision_activity_id: Last system's activity ID
        :param timeout: Max waiting time for process to be done
        :return:
        """

        start_time = time.time()

        # Provision waiter
        while (time.time() - start_time) < timeout:
            time.sleep(WAIT_BETWEEN_PROVISION_CHECKS)
            last_activity = self._get_last_system_activity()
            if (last_activity['id'] != pre_provision_activity_id['id']) \
                    and last_activity['action'] == 'clear_netboot':
                break
        else:
            return True

        # Ping waiter
        while (time.time() - start_time) < timeout:
            command = "ping -q -c 30 -w 300 {0}".format(self.fqdn)
            if not subprocess.call(command.split(" ")):
                return False
        else:
            return True

    def _build_url(self, action, fqdn=None):
        """
        Build URL by concatenating the base URL of the beaker server with
        the specific action string

        :param action: An action from the class variable ACTIONS
        :param fqdn: The system's fully qualified domain name
        :return: String of the absolute URL
        """

        url = self.REQ_URL.get(action)
        if fqdn:
            url = urljoin(SYS_FQDN_PATH.format(fqdn=fqdn), url)

        return urljoin(self.base_url, url)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            username=dict(default='admin'),
            password=dict(required=True),
            fqdn=dict(required=True),
            action=dict(required=True, choices=['provision', 'release']),
            distro_tree_id=dict(default=71576)))

    beaker_client = BeakerManager(url=module.params['server_url'],
                                  username=module.params['username'],
                                  password=module.params['password'],
                                  fqdn=module.params['fqdn'])

    status_changed = False

    # Reserve & provision
    if module.params['action'] == 'provision':
        # Reserve the system
        if beaker_client.reserve():
            module.fail_json(msg='Failed to reserve system (%s).' %
                                 module.params['fqdn'])

        # Provision the system
        if beaker_client.provision(distro_id=module.params['distro_tree_id'],
                                   reboot=True):
            module.fail_json(msg="System provisioning has failed (%s)." %
                                 module.params['fqdn'])
        status_changed = True

    # Release
    else:
        if beaker_client.release():
            module.fail_json(msg="Failed to release the system (%s)." %
                                 module.params['fqdn'])

    module.exit_json(changed=status_changed, host=module.params['fqdn'])


from ansible.module_utils.basic import *

main()
