#!/usr/bin/env python
# Copyright 2015 Red Hat, Inc.
# Copyright 2015 Lenovo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Virtual BMC for controlling OpenStack instances, based on fakebmc from
# python-pyghmi

# Sample ipmitool commands:
# ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power on
# ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power status
# ipmitool -I lanplus -U admin -P password -H 127.0.0.1 chassis bootdev pxe|disk
# ipmitool -I lanplus -U admin -P password -H 127.0.0.1 mc reset cold

import argparse
import sys
import time

from novaclient import client as novaclient
from novaclient import exceptions
import pyghmi.ipmi.bmc as bmc


class OpenStackBmc(bmc.Bmc):
    def __init__(self, authdata, port, address, instance, user, password, tenant,
                 auth_url):
        super(OpenStackBmc, self).__init__(authdata, port=port, address=address)
        self.novaclient = novaclient.Client(2, user, password,
                                            tenant, auth_url)
        self.instance = None
        self.cached_status = None
        self.target_status = None
        # At times the bmc service is started before important things like
        # networking have fully initialized.  Keep trying to find the
        # instance indefinitely, since there's no point in continuing if
        # we don't have an instance.
        while True:
            try:
                self.instance = self._find_instance(instance)
                if self.instance is not None:
                    name = self.novaclient.servers.get(self.instance).name
                    self.log('Managing instance: %s UUID: %s' %
                             (name, self.instance))
                    break
            except Exception as e:
                self.log('Exception finding instance "%s": %s' % (instance, e))
                time.sleep(1)

    def _find_instance(self, instance):
        try:
            self.novaclient.servers.get(instance)
            return instance
        except exceptions.NotFound:
            name_regex = '^%s$' % instance
            i = self.novaclient.servers.list(search_opts={'name': name_regex})
            if len(i) > 1:
                self.log('Ambiguous instance name %s' % instance)
                sys.exit(1)
            try:
                return i[0].id
            except IndexError:
                self.log('Could not find specified instance %s' % instance)
                sys.exit(1)

    def get_boot_device(self):
        server = self.novaclient.servers.get(self.instance)
        retval = 'network' if server.metadata.get('libvirt:pxe-first') else 'hd'
        self.log('Reporting boot device', retval)
        return retval

    def set_boot_device(self, bootdevice):
        server = self.novaclient.servers.get(self.instance)
        if bootdevice == 'network':
            self.novaclient.servers.set_meta_item(server, 'libvirt:pxe-first', '1')
        else:
            self.novaclient.servers.set_meta_item(server, 'libvirt:pxe-first', '')
        self.log('Set boot device to', bootdevice)

    def cold_reset(self):
        # Reset of the BMC, not managed system, here we will exit the demo
        self.log('Shutting down in response to BMC cold reset request')
        sys.exit(0)

    def _instance_active(self):
        if self.cached_status is None or self.cached_status != self.target_status:
            self.cached_status = self.novaclient.servers.get(self.instance).status
        return self.cached_status == 'ACTIVE'

    def get_power_state(self):
        self.log('Getting power state for %s' % self.instance)
        return self._instance_active()

    def power_off(self):
        # this should be power down without waiting for clean shutdown
        self.target_status = 'SHUTOFF'
        if self._instance_active():
            try:
                self.novaclient.servers.stop(self.instance)
                self.log('Powered off %s' % self.instance)
            except exceptions.Conflict as e:
                # This can happen if we get two requests to start a server in
                # short succession.  The instance may then be in a powering-on
                # state, which means it is invalid to start it again.
                self.log('Ignoring exception: "%s"' % e)
        else:
            self.log('%s is already off.' % self.instance)
            return 0xd5

    def power_on(self):
        self.target_status = 'ACTIVE'
        if not self._instance_active():
            try:
                self.novaclient.servers.start(self.instance)
                self.log('Powered on %s' % self.instance)
            except exceptions.Conflict as e:
                # This can happen if we get two requests to start a server in
                # short succession.  The instance may then be in a powering-on
                # state, which means it is invalid to start it again.
                self.log('Ignoring exception: "%s"' % e)
        else:
            self.log('%s is already on.' % self.instance)
            return 0xd5

    def power_reset(self):
        pass

    def power_shutdown(self):
        # should attempt a clean shutdown
        self.target_status = 'ACTIVE'
        self.novaclient.servers.stop(self.instance)
        self.log('Politely shut down %s' % self.instance)

    def log(self, *msg):
        print(' '.join(msg))
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(
        prog='openstackbmc',
        description='Virtual BMC for controlling OpenStack instance',
    )
    parser.add_argument('--port',
                        dest='port',
                        type=int,
                        default=623,
                        help='Port to listen on; defaults to 623')
    parser.add_argument('--address',
                        dest='address',
                        default='::',
                        help='Address to bind to; defaults to ::')
    parser.add_argument('--instance',
                        dest='instance',
                        required=True,
                        help='The uuid or name of the OpenStack instance to manage')
    parser.add_argument('--os-user',
                        dest='user',
                        required=True,
                        help='The user for connecting to OpenStack')
    parser.add_argument('--os-password',
                        dest='password',
                        required=True,
                        help='The password for connecting to OpenStack')
    parser.add_argument('--os-tenant',
                        dest='tenant',
                        required=True,
                        help='The tenant for connecting to OpenStack')
    parser.add_argument('--os-auth-url',
                        dest='auth_url',
                        required=True,
                        help='The OpenStack Keystone auth url')
    args = parser.parse_args()
    # Default to ipv6 format, but if we get an ipv4 address passed in use the
    # appropriate format for pyghmi to listen on it.
    addr_format = '%s'
    if ':' not in args.address:
        addr_format = '::ffff:%s'
    mybmc = OpenStackBmc({'admin': 'password'}, port=args.port,
                         address=addr_format % args.address,
                         instance=args.instance,
                         user=args.user,
                         password=args.password,
                         tenant=args.tenant,
                         auth_url=args.auth_url)
    mybmc.listen()


if __name__ == '__main__':
    main()
