#!/usr/bin/env python
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""Collectd python plugin to read swift stat on an OpenStack Controller."""
from swiftclient.client import Connection
import collectd
import os
import time


class CollectdSwiftStat(object):
    SWIFT_STATS = {
        'x-account-object-count': 'objects',
        'x-account-container-count': 'containers',
        'x-account-bytes-used': 'bytes'}

    def __init__(self):
        self.interval = 10
        self.prefix = None
        self.user = None
        self.password = None
        self.authurl = None
        self.authversion = None
        self.project = None
        self.swift_conn = None

    def configure_callback(self, configobj):
        for node in configobj.children:
            val = str(node.values[0])
            if node.key == 'Interval':
                self.interval = int(float(val))
            elif node.key == 'Prefix':
                self.prefix = val
            elif node.key == 'User':
                self.user = val
            elif node.key == 'Password':
                self.password = val
            elif node.key == 'AuthURL':
                self.authurl = val
            elif node.key == 'AuthVersion':
                self.authversion = val
            elif node.key == 'Project':
                self.project = val
            else:
                collectd.warning(
                    'collectd-swift-stat: Unknown config key: {}'
                    .format(node.key))

        read_plugin = True
        if not self.prefix:
            collectd.error('collectd-swift-stat: Prefix Undefined')
            read_plugin = False
        if not self.user:
            collectd.error('collectd-swift-stat: User Undefined')
            read_plugin = False
        if not self.password:
            collectd.error('collectd-swift-stat: Password Undefined')
            read_plugin = False
        if not self.authurl:
            collectd.error('collectd-swift-stat: AuthURL Undefined')
            read_plugin = False
        if not self.authversion:
            collectd.error('collectd-swift-stat: AuthVersion Undefined')
            read_plugin = False
        if not self.project:
            collectd.error('collectd-swift-stat: Project Undefined')
            read_plugin = False

        if read_plugin:
            collectd.info(
                'swift_stat: Connecting with user={}, password={}, tenant={}, auth_url={},'
                ' auth_version={}'.format(
                    self.user, self.password, self.project, self.authurl, self.authversion))

            self.swift_conn = self.create_swift_session()
            collectd.register_read(self.read_swift_stat, self.interval)
        else:
            collectd.error('collectd_swift_stat: Invalid configuration')

    def read_swift_stat(self, data=None):
        starttime = time.time()

        stats = self.swift_conn.head_account()

        for m_instance, name in CollectdSwiftStat.SWIFT_STATS.iteritems():
            if m_instance in stats:
                metric = collectd.Values()
                metric.plugin = 'swift_stat'
                metric.interval = self.interval
                metric.type = 'gauge'
                metric.type_instance = '{}-{}'.format(self.prefix, name)
                metric.values = [stats[m_instance]]
                metric.dispatch()
            else:
                collectd.error(
                    'swift_stat: Can not find: {}'.format(m_instance))

        timediff = time.time() - starttime
        if timediff > self.interval:
            collectd.warning(
                'swift_stat: Took: {} > {}'
                .format(round(timediff, 2), self.interval))

    def create_swift_session(self):
        return Connection(
            authurl=self.authurl, user=self.user, key=self.password,
            tenant_name=self.project, auth_version=self.authversion)


collectd_swift_stat = CollectdSwiftStat()
collectd.register_config(collectd_swift_stat.configure_callback)
