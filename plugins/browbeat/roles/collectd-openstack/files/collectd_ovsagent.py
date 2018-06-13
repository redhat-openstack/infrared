#!/usr/bin/env python
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""
"""

import collectd
import os
import subprocess
import time

def configure(cfg):
    global INTERVAL
    global interfaces
    global namespaces
    interfaces = []
    namespaces = []
    config = {c.key: c.values for c in cfg.children}
    INTERVAL = config['interval'][0]
    collectd.register_read(read, INTERVAL)
    if 'interfaces' in config:
        interfaces = config['interfaces']
    if 'namespaces' in config :
        namespaces = config['namespaces']

def run_command(command):
    output = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE)
    return output.communicate()

def read(data=None):
    starttime = time.time()
    ifs = []
    ns = []
    if len(interfaces) > 0 :
        collectd.debug("Interfaces : {}".format(interfaces))
        for interface in interfaces :
            ifs.append({interface: run_command("ovs-vsctl show | grep 'Port \\\"{}' | wc -l".format(interface))[0].replace("\n","")})
    if len(namespaces) > 0 :
        collectd.debug("Namespaces : {}".format(namespaces))
        for namespace in namespaces :
            ns.append({namespace: run_command("sudo ip netns | grep {} | wc -l".format(namespace))[0].replace("\n","")})
    if len(ifs) > 0 :
        for i in ifs :
            for value in i:
                metric = collectd.Values()
                metric.plugin = 'ovsagent_monitoring'
                metric.interval = INTERVAL
                metric.type = 'gauge'
                metric.type_instance = "{}_interface_total-count".format(value)
                metric.values = [i[value]]
                metric.dispatch()

    if len(ns) > 0 :
        for n in ns :
            for value in n:
                metric = collectd.Values()
                metric.plugin = 'ovsagent_monitoring'
                metric.interval = INTERVAL
                metric.type = 'gauge'
                metric.type_instance = "{}_ns_total-count".format(value)
                metric.values = [n[value]]
                metric.dispatch()

    timediff = time.time() - starttime
    if timediff > INTERVAL:
        collectd.warning(
            'ovsagent_monitoring: Took: {} > {}'.format(
                round(timediff, 2),
                INTERVAL)
            )

collectd.register_config(configure)
