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
"""Collectd python plugin to read ceph storage stats from ceph command line for
an OpenStack Cloud.
"""

import collectd
import json
import os
import subprocess
import time
import traceback


class CollectdCephStorage(object):
    def __init__(self):
        self.ceph_cluster = None
        self.ceph_rados_bench = False
        self.ceph_rados_bench_interval = 60
        self.ceph_mon_stats = False
        self.ceph_mon_stats_interval = 10
        self.ceph_osd_stats = False
        self.ceph_osd_stats_interval = 10
        self.ceph_pg_stats = False
        self.ceph_pg_stats_interval = 10
        self.ceph_pool_stats = False
        self.ceph_pool_stats_interval = 10

    def configure_callback(self, config):
        for node in config.children:
            val = str(node.values[0])
            if node.key == 'CephRadosBench':
                self.ceph_rados_bench = val in ['True', 'true']
            elif node.key == 'CephMONStats':
                self.ceph_mon_stats = val in ['True', 'true']
            elif node.key == 'CephOSDStats':
                self.ceph_osd_stats = val in ['True', 'true']
            elif node.key == 'CephPGStats':
                self.ceph_pg_stats = val in ['True', 'true']
            elif node.key == 'CephPoolStats':
                self.ceph_pool_stats = val in ['True', 'true']
            elif node.key == 'CephCluster':
                self.ceph_cluster = val
            elif node.key == 'CephRadosBenchInterval':
                self.ceph_rados_bench_interval = int(float(val))
            elif node.key == 'CephMONStatsInterval':
                self.ceph_mon_stats_interval = int(float(val))
            elif node.key == 'CephOSDStatsInterval':
                self.ceph_osd_stats_interval = int(float(val))
            elif node.key == 'CephPGStatsInterval':
                self.ceph_pg_stats_interval = int(float(val))
            elif node.key == 'CephPoolStatsInterval':
                self.ceph_pool_stats_interval = int(float(val))
            else:
                collectd.warning(
                    'collectd-ceph-storage: Unknown config key: {}'
                    .format(node.key))

        if not self.ceph_cluster:
            collectd.warning('collectd-ceph-storage: CephCluster Undefined')

        if self.ceph_rados_bench:
            collectd.info('Registered Ceph Rados Bench')
            collectd.register_read(
                self.read_ceph_rados_bench,
                self.ceph_rados_bench_interval, name='ceph-rados-bench')
        if self.ceph_mon_stats:
            collectd.info('Registered Ceph Mon')
            collectd.register_read(
                self.read_ceph_mon, self.ceph_mon_stats_interval,
                name='ceph-monitor')
        if self.ceph_osd_stats:
            collectd.info('Registered Ceph OSD')
            collectd.register_read(
                self.read_ceph_osd, self.ceph_osd_stats_interval,
                name='ceph-osd')
        if self.ceph_pg_stats:
            collectd.info('Registered Ceph PG')
            collectd.register_read(
                self.read_ceph_pg, self.ceph_pg_stats_interval, name='ceph-pg')
        if self.ceph_pool_stats:
            collectd.info('Registered Ceph Pool')
            collectd.register_read(
                self.read_ceph_pool, self.ceph_pool_stats_interval,
                name='ceph-pool')

    def dispatch_value(self, plugin_instance, type_instance, value, interval):
        metric = collectd.Values()
        metric.plugin = 'collectd-ceph-storage'
        metric.interval = interval
        metric.type = 'gauge'
        metric.plugin_instance = plugin_instance
        metric.type_instance = type_instance
        metric.values = [value]
        metric.dispatch()

    def read_ceph_rados_bench(self):
        """Runs "rados bench" and collects latencies reported."""
        rados_bench_ran, output = self.run_command(
                ['timeout', '30s', 'rados', '-p', 'rbd', 'bench', '10',
                    'write', '-t', '1', '-b', '65536', '2>/dev/null', '|',
                    'grep', '-i', 'latency', '|', 'awk',
                    '\'{print 1000*$3}\''], False)

        if rados_bench_ran:
            results = output.split('\n')

            self.dispatch_value(
                'cluster', 'avg_latency', results[0],
                self.ceph_rados_bench_interval)
            self.dispatch_value(
                'cluster', 'stddev_latency', results[1],
                self.ceph_rados_bench_interval)
            self.dispatch_value(
                'cluster', 'max_latency', results[2],
                self.ceph_rados_bench_interval)
            self.dispatch_value(
                'cluster', 'min_latency', results[3],
                self.ceph_rados_bench_interval)

    def read_ceph_mon(self):
        """Reads stats from "ceph mon dump" command."""
        mon_dump_ran, output = self.run_command(
                ['ceph', 'mon', 'dump', '-f', 'json', '--cluster',
                    self.ceph_cluster])

        if mon_dump_ran:
            json_data = json.loads(output)

            self.dispatch_value(
                'mon', 'number', len(json_data['mons']),
                self.ceph_mon_stats_interval)
            self.dispatch_value(
                'mon', 'quorum', len(json_data['quorum']),
                self.ceph_mon_stats_interval)

    def read_ceph_osd(self):
        """Reads stats from "ceph osd dump" command."""
        osd_dump_ran, output = self.run_command(
                ['ceph', 'osd', 'dump', '-f', 'json', '--cluster',
                    self.ceph_cluster])

        if osd_dump_ran:
            json_data = json.loads(output)

            self.dispatch_value(
                'pool', 'number', len(json_data['pools']),
                self.ceph_osd_stats_interval)

            for pool in json_data['pools']:
                pool_name = 'pool-{}'.format(pool['pool_name'])
                self.dispatch_value(
                    pool_name, 'size', pool['size'],
                    self.ceph_osd_stats_interval)
                self.dispatch_value(
                    pool_name, 'pg_num', pool['pg_num'],
                    self.ceph_osd_stats_interval)
                self.dispatch_value(
                    pool_name, 'pgp_num', pool['pg_placement_num'],
                    self.ceph_osd_stats_interval)

            osds_up = 0
            osds_down = 0
            osds_in = 0
            osds_out = 0
            for osd in json_data['osds']:
                if osd['up'] == 1:
                    osds_up += 1
                else:
                    osds_down += 1
                if osd['in'] == 1:
                    osds_in += 1
                else:
                    osds_out += 1

            self.dispatch_value(
                'osd', 'up', osds_up, self.ceph_osd_stats_interval)
            self.dispatch_value(
                'osd', 'down', osds_down, self.ceph_osd_stats_interval)
            self.dispatch_value(
                'osd', 'in', osds_in, self.ceph_osd_stats_interval)
            self.dispatch_value(
                'osd', 'out', osds_out, self.ceph_osd_stats_interval)

    def read_ceph_pg(self):
        """Reads stats from "ceph pg dump" command."""
        pg_dump_ran, output = self.run_command(
                ['ceph', 'pg', 'dump', '-f', 'json', '--cluster',
                    self.ceph_cluster])

        if pg_dump_ran:
            json_data = json.loads(output)

            pgs = {}
            for pg in json_data['pg_stats']:
                for state in pg['state'].split('+'):
                    if state not in pgs:
                        pgs[state] = 0
                    pgs[state] += 1

            for state in pgs:
                self.dispatch_value(
                    'pg', state, pgs[state], self.ceph_pg_stats_interval)

            for osd in json_data['osd_stats']:
                osd_id = 'osd-{}'.format(osd['osd'])
                self.dispatch_value(
                    osd_id, 'kb_used', osd['kb_used'],
                    self.ceph_pg_stats_interval)
                self.dispatch_value(
                    osd_id, 'kb_total', osd['kb'], self.ceph_pg_stats_interval)
                self.dispatch_value(
                    osd_id, 'snap_trim_queue_len', osd['snap_trim_queue_len'],
                    self.ceph_pg_stats_interval)
                self.dispatch_value(
                    osd_id, 'num_snap_trimming', osd['num_snap_trimming'],
                    self.ceph_pg_stats_interval)
                self.dispatch_value(
                    osd_id, 'apply_latency_ms',
                    osd['fs_perf_stat']['apply_latency_ms'],
                    self.ceph_pg_stats_interval)
                self.dispatch_value(
                    osd_id, 'commit_latency_ms',
                    osd['fs_perf_stat']['commit_latency_ms'],
                    self.ceph_pg_stats_interval)

    def read_ceph_pool(self):
        """Reads stats from "ceph osd pool" and "ceph df" commands."""
        stats_ran, stats_output = self.run_command(
                ['ceph', 'osd', 'pool', 'stats', '-f', 'json'])
        df_ran, df_output = self.run_command(['ceph', 'df', '-f', 'json'])

        if stats_ran:
            json_stats_data = json.loads(stats_output)

            for pool in json_stats_data:
                pool_key = 'pool-{}'.format(pool['pool_name'])
                for stat in (
                        'read_bytes_sec', 'write_bytes_sec', 'read_op_per_sec',
                        'write_op_per_sec'):
                    value = 0
                    if stat in pool['client_io_rate']:
                        value = pool['client_io_rate'][stat]
                    self.dispatch_value(
                        pool_key, stat, value, self.ceph_pool_stats_interval)

        if df_ran:
            json_df_data = json.loads(df_output)

            for pool in json_df_data['pools']:
                pool_key = 'pool-{}'.format(pool['name'])
                for stat in ('bytes_used', 'kb_used', 'objects'):
                    value = pool['stats'][stat] if stat in pool['stats'] else 0
                    self.dispatch_value(
                        pool_key, stat, value, self.ceph_pool_stats_interval)

            if 'total_bytes' in json_df_data['stats']:
                # ceph 0.84+
                self.dispatch_value(
                    'cluster', 'total_space',
                    int(json_df_data['stats']['total_bytes']),
                    self.ceph_pool_stats_interval)
                self.dispatch_value(
                    'cluster', 'total_used',
                    int(json_df_data['stats']['total_used_bytes']),
                    self.ceph_pool_stats_interval)
                self.dispatch_value(
                    'cluster', 'total_avail',
                    int(json_df_data['stats']['total_avail_bytes']),
                    self.ceph_pool_stats_interval)
            else:
                # ceph < 0.84
                self.dispatch_value(
                    'cluster', 'total_space',
                    int(json_df_data['stats']['total_space']) * 1024.0,
                    self.ceph_pool_stats_interval)
                self.dispatch_value(
                    'cluster', 'total_used',
                    int(json_df_data['stats']['total_used']) * 1024.0,
                    self.ceph_pool_stats_interval)
                self.dispatch_value(
                    'cluster', 'total_avail',
                    int(json_df_data['stats']['total_avail']) * 1024.0,
                    self.ceph_pool_stats_interval)

    def run_command(self, command, check_output=True):
        """Run a command for this collectd plugin. Returns a tuple with command
        success and output or False and None for output.
        """
        output = None
        try:
            if check_output:
                output = subprocess.check_output(command)
            else:
                stdin, stdout, stderr = os.popen3(' '.join(command))
                output = stdout.read()
        except Exception as exc:
            collectd.error(
                'collectd-ceph-storage: {} exception: {}'.format(command, exc))
            collectd.error(
                'collectd-ceph-storage: {} traceback: {}'
                .format(command, traceback.format_exc()))
            return False, None

        if output is None:
            collectd.error(
                'collectd-ceph-storage: failed to {}: output is None'
                .format(command))
            return False, None
        return True, output

collectd_ceph_storage = CollectdCephStorage()
collectd.register_config(collectd_ceph_storage.configure_callback)
