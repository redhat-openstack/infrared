#!/usr/bin/env python
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
from six.moves.urllib.parse import urljoin
from xml.dom import minidom

import requests
import requests.auth
import requests.cookies

DOCUMENTATION = '''
---
module: beaker_provisioner
version_added: "0.1"
short_description: Provision servers via Beaker
description:
   - Provision servers via Beaker
options:
    url:
        description:
            - Base URL of Beaker server
        required: true
    username:
        description:
            - Login username to authenticate to Beaker
        required: false
        default: admin
    password:
        description:
            - Password of login user
            required: true
    host:
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
    web_service:
        description
            - Web service protocol
        default: 'rest'
        choices: 'rest', 'rpc'
    ca_cert:
        description:
            - CA certificate (python 2.7.9+ only)
        required: false
    custom_loan_comment:
        description:
            - Message stored as "Loan Comment" in Beaker's history
              Default value is used if not specified
              Comment can be max 60 lines long (Beaker requirement!),
              otherwise it will be cut
        required: false
'''

DEFAULT_LOAN_COMMENT = "Loaned by InfraRed Module For Beaker"
SYS_FQDN_PATH = '/systems/{fqdn}/'
WAIT_BETWEEN_PROVISION_CHECKS = 10


class BeakerMachine(object):
    REQ_URL = dict(
        ALL='',
        FREE='free/',
        LOAN='loans/',
        VIEW='view/',
        RETURN='loans/+current',
        RESERVE='reservations/',
        RELEASE='reservations/+current',
        PROVISION='installations/',
        SYSTEMS='systems/',
    )

    def __init__(self, url, username, password, fqdn, web_service, ca_cert, custom_loan_comment,
                 disable_warnings=True):
        """
        BeakerMachine initializer.

        :param url: Base URL of the Beaker server
        :param username: Authentication username
        :param password: Authentication password
        :param fqdn: Fully qualified domain name of a system
        :param disable_warnings: Hide unverified HTTPS requests warnings (
        default = False)
        """
        self.base_url = url
        self.auth = requests.auth.HTTPBasicAuth(username, password)
        self.fqdn = fqdn
        self.web_service = web_service
        self.ca_cert = ca_cert
        self.loan_comment = custom_loan_comment or DEFAULT_LOAN_COMMENT
        self.disable_warnings = disable_warnings
        self.changed = False
        self.session = None
        self.details = {}

    def create_session(self):
        """
        Creates a session and get some details on the machine.
        """
        self.session = requests.Session()
        self.session.auth = self.auth

        # whether verify the SSL certificate or not
        self.session.verify = self.ca_cert or False

        if self.disable_warnings:
            requests.packages.urllib3.disable_warnings()

        if self.web_service == 'rpc':
            self.session.cookies = requests.cookies.cookiejar_from_dict(
                self._xml_rpc_auth())
        else:
            # cookie workaround - consider changing with _get_last_activity()
            self.list_systems(limit=1)

        self.details = self.get_system_details()

    def get_system_details(self):
        """
        Get system's details

        :return: dict containing details about the system
        """
        headers = {'Content-Type': 'application/json'}
        url = urljoin(self.base_url, SYS_FQDN_PATH.format(fqdn=self.fqdn))
        resp = self.session.get(url, headers=headers)

        assert resp.status_code == requests.codes.OK, \
            "Failed to get system's details: %s" % resp.text

        return json.loads(resp.text)

    def list_systems(self, limit=0, filters=None, req='FREE'):
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
        params = dict(tg_format='atom', list_tgp_limit=limit)

        cnt = 0
        for f_name, f_val in filters.items():
            params['systemsearch-{0}.table'.format(cnt)] = f_name
            params['systemsearch-{0}.operation'.format(cnt)] = 'is'
            params['systemsearch-{0}.value'.format(cnt)] = f_val
            cnt += 1

        # save the session params before changes
        saved_params = self.session.params

        self.session.params = params
        resp = self.session.get(url)
        assert resp.status_code == requests.codes.OK, \
            str(resp.status_code) + " - " + resp.reason

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

        :raises AssertionError: If fails to release the system
        """
        if self.details['current_reservation']:
            self._release_system()
            self.changed = True

        if self.details['current_loan']:
            self._return_system()
            self.changed = True

    def reserve(self):
        """
        Reserve the system

        :raises AssertionError: If fails to reserve the system try to return
        """
        self._loan_system()
        try:
            self._reserve_system()
        except AssertionError:
            self._return_system()
            raise

    def _loan_system(self):
        """
        Loan a system

        :raises AssertionError: If fails to loan the system
        """
        headers = {'Content-Type': 'application/json'}
        url = self._build_url('LOAN', self.fqdn)
        resp = self.session.post(url, headers=headers,
                                 data=json.dumps({'comment': self.loan_comment}))

        assert resp.status_code == requests.codes.OK, "Failed to loan system: %s" % resp.text

    def _return_system(self):
        """
        Return a loaned system

        :raises AssertionError: If fails to return the system
        """
        headers = {'Content-Type': 'application/json'}
        url = self._build_url('RETURN', self.fqdn)
        resp = self.session.patch(url, headers=headers,
                                  data=json.dumps({'finish': 'now'}))

        assert resp.status_code == requests.codes.OK, "Failed to return system: %s" % resp.text

    def _reserve_system(self):
        """
        Reserve a system

        :raises AssertionError: If fails to reserve the system
        """
        headers = {'Content-Type': 'application/json'}
        url = self._build_url('RESERVE', self.fqdn)
        resp = self.session.post(url, headers=headers)

        assert resp.status_code == requests.codes.OK, \
            "Failed to reserve system: %s" % resp.text

    def _release_system(self):
        """
        Release a reserved system

        :raises AssertionError: If fails to release the system
        """
        headers = {'Content-Type': 'application/json'}
        url = self._build_url('RELEASE', self.fqdn)
        resp = self.session.patch(url, headers=headers,
                                  data=json.dumps({'finish_time': 'now'}))

        assert resp.status_code == requests.codes.OK, \
            "Failed to release system: %s" % resp.text

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
        :raises AssertionError: If fails to  provision the system
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

        assert resp.status_code in [requests.codes.CREATED,
                                    requests.codes.OK], \
            ', '.join((str(resp.status_code), resp.reason, resp.text))

        self.changed = True

        if wait_for_host:
            self._wait_for_provision(
                last_pre_provison_activity, provision_timeout)

    def _get_last_system_activity(self):
        """
        Return the ID of the last system's activity
        """

        headers = {'accept': 'application/json'}
        url = self.base_url + '/activity/system'
        self.session.params = {'q': 'system:' + self.fqdn}
        resp = self.session.get(url, headers=headers)

        return json.loads(resp.text)['entries'][0]

    def _wait_for_provision(self, pre_provision_activity_id, timeout):
        """
        Waits until the provisioning process is done.

        :param pre_provision_activity_id: Last system's activity ID.
        :param timeout: Max time (in seconds) to wait for provisioning process.
        :raises RuntimeError: If waiting timeout exceeded
        """

        start_time = time.time()

        # Provision waiter
        while (time.time() - start_time) < timeout:
            time.sleep(WAIT_BETWEEN_PROVISION_CHECKS)
            last_activity = self._get_last_system_activity()
            if all((last_activity['id'] != pre_provision_activity_id['id'],
                    last_activity['action'] == 'clear_netboot',
                    last_activity['service'] == 'XMLRPC')):
                break
        else:
            raise RuntimeError(
                "Provisioning waiting time exceeded ({} seconds)".format(
                    timeout))

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

    def _xml_rpc_auth(self):
        """
        Authenticates with the server using XML-RPC and returns the cookie's
        name and ID.
        """
        # TODO: This method should be replaced with SafeCookieTransfer class!!!
        import re
        import ssl
        import six.moves.xmlrpc_client as xmlrpclib

        # This method is supposed to return the beaker_auth_token, but
        # that is not easily obtainable from the library as atribute or by
        # a method. We need to obtain it (steal it) from the parse_response()
        # method inside Transport object, otherwise it has to be hacked
        # very dirty by stealing sys.stdout and parsing it (as it was done
        # in prev implementation). This approach is slightly cleaner.
        # To do it, VerboseSafeTransport is used instead of SafeTransport.
        class VerboseSafeTransport(xmlrpclib.SafeTransport):

            def parse_response(self, response):
                self.response = response
                return super().parse_response(response)

        try:
            ssl_context = ssl.create_default_context(cafile=self.ca_cert)
            transport = VerboseSafeTransport(context=ssl_context)
        except TypeError:
            # py < 2.7.9
            transport = VerboseSafeTransport()

        hub = xmlrpclib.ServerProxy(
            urljoin(self.base_url, 'client'),
            allow_none=True,
            transport=transport,
            verbose=False)

        try:
            hub.auth.login_password(self.auth.username, self.auth.password)
        except xmlrpclib.Fault:
            raise RuntimeError('Failed to authenticate with the server')

        # Finally get the cookie that contains "beaker_auth_token" here
        cookie = transport.response.headers.get_all("Set-Cookie")
        pattern = re.compile('beaker_auth_token=[\w.-]*')
        results = pattern.findall(str(cookie))
        if not results:
            raise RuntimeError("Cookie not found")

        return {'beaker_auth_token': results[0].split('=')[1]}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(required=True),
            username=dict(default='admin'),
            password=dict(required=True),
            host=dict(required=True),
            action=dict(required=True, choices=['provision', 'release']),
            distro_tree_id=dict(default=71576),
            web_service=dict(default='rest', choices=['rest', 'rpc']),
            ca_cert=dict(required=False),
            custom_loan_comment=dict(default="",required=False),
        ))

    if module.params['ca_cert'] and not os.path.exists(os.path.expanduser(module.params['ca_cert'])):
        module.fail_json(msg="CA cert file doesn't exist", ca_cert=module.params['ca_cert'])

    beaker_client = BeakerMachine(url=module.params['url'],
                                  username=module.params['username'],
                                  password=module.params['password'],
                                  fqdn=module.params['host'],
                                  web_service=module.params['web_service'],
                                  ca_cert=module.params['ca_cert'],
                                  custom_loan_comment=module.params['custom_loan_comment'])

    try:
        beaker_client.create_session()

        # Reserve & provision
        if module.params['action'] == 'provision':
            # Reserve the system
            beaker_client.reserve()

            # Provision the system
            beaker_client.provision(
                reboot=True, distro_id=module.params['distro_tree_id'], )

        # Release
        else:
            beaker_client.release()

        module.exit_json(
            changed=beaker_client.changed, host=beaker_client.fqdn)

    except (AssertionError, RuntimeError) as exc:
        module.fail_json(
            msg=exc.message + ", host: {}".format(beaker_client.fqdn))


from ansible.module_utils.basic import *

main()
