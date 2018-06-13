#!/usr/bin/env python
# coding=utf-8
# The MIT License (MIT)
#
# Copyright (c) 2014-2016 Denis Zhdanov
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# collectd-iostat-python
# ======================
#
# Collectd-iostat-python is an iostat plugin for collectd that allows you to
# graph Linux iostat metrics in Graphite or other output formats that are
# supported by collectd.
#
# https://github.com/powdahound/redis-collectd-plugin
#   - was used as template
# https://github.com/keirans/collectd-iostat/
#   - was used as inspiration and contains some code from
# https://bitbucket.org/jakamkon/python-iostat
#   - by Kuba Kończyk <jakamkon at users.sourceforge.net>
#

import signal
import string
import subprocess
import sys
import re
try:
    import pyudev
    pyudev_available = True
except ImportError:
    pyudev_available = False

# Original Version/Author
__version__ = '0.0.5'
__author__ = 'denis.zhdanov@gmail.com'


class IOStatError(Exception):
    pass


class CmdError(IOStatError):
    pass


class ParseError(IOStatError):
    pass


class IOStat(object):
    def __init__(self, path='/usr/bin/iostat', interval=2, count=2, disks=[], no_dm_name=False):
        self.path = path
        self.interval = interval
        self.count = count
        self.disks = disks
        self.no_dm_name = no_dm_name

    def parse_diskstats(self, input):
        """
        Parse iostat -d and -dx output.If there are more
        than one series of statistics, get the last one.
        By default parse statistics for all avaliable block devices.

        @type input: C{string}
        @param input: iostat output

        @type disks: list of C{string}s
        @param input: lists of block devices that
        statistics are taken for.

        @return: C{dictionary} contains per block device statistics.
        Statistics are in form of C{dictonary}.
        Main statistics:
          tps  Blk_read/s  Blk_wrtn/s  Blk_read  Blk_wrtn
        Extended staistics (available with post 2.5 kernels):
          rrqm/s  wrqm/s  r/s  w/s  rsec/s  wsec/s  rkB/s  wkB/s  avgrq-sz \
          avgqu-sz  await  svctm  %util
        See I{man iostat} for more details.
        """
        dstats = {}
        dsi = input.rfind('Device:')
        if dsi == -1:
            raise ParseError('Unknown input format: %r' % input)

        ds = input[dsi:].splitlines()
        hdr = ds.pop(0).split()[1:]

        for d in ds:
            if d:
                d = d.split()
                d = [re.sub(r',','.',element) for element in d]
                dev = d.pop(0)
                if (dev in self.disks) or not self.disks:
                    dstats[dev] = dict([(k, float(v)) for k, v in zip(hdr, d)])

        return dstats

    def sum_dstats(self, stats, smetrics):
        """
        Compute the summary statistics for chosen metrics.
        """
        avg = {}

        for disk, metrics in stats.iteritems():
            for mname, metric in metrics.iteritems():
                if mname not in smetrics:
                    continue
                if mname in avg:
                    avg[mname] += metric
                else:
                    avg[mname] = metric

        return avg

    def _run(self, options=None):
        """
        Run iostat command.
        """
        close_fds = 'posix' in sys.builtin_module_names
        args = '%s %s %s %s %s' % (
            self.path,
            ''.join(options),
            self.interval,
            self.count,
            ' '.join(self.disks))

        return subprocess.Popen(
            args,
            bufsize=1,
            shell=True,
            stdout=subprocess.PIPE,
            close_fds=close_fds)

    @staticmethod
    def _get_childs_data(child):
        """
        Return child's data when avaliable.
        """
        (stdout, stderr) = child.communicate()
        ecode = child.poll()

        if ecode != 0:
            raise CmdError('Command %r returned %d' % (child.cmd, ecode))

        return stdout

    def get_diskstats(self):
        """
        Get all avaliable disks statistics that we can get.
        iostat -kNd
         tps    kB_read/s    kB_wrtn/s    kB_read    kB_wrtn
        iostat -kNdx
         rrqm/s   wrqm/s     r/s     w/s    rkB/s    wkB/s avgrq-sz
         avgqu-sz   await r_await w_await  svctm  %util
        """
        options=['-','k','N','d']
        extdoptions=['-','k','N','d','x']
        if self.no_dm_name:
            options.remove('N')
            extdoptions.remove('N')
        dstats = self._run(options)
        extdstats = self._run(extdoptions)
        dsd = self._get_childs_data(dstats)
        edd = self._get_childs_data(extdstats)
        ds = self.parse_diskstats(dsd)
        eds = self.parse_diskstats(edd)

        for dk, dv in ds.iteritems():
            if dk in eds:
                ds[dk].update(eds[dk])

        return ds


class IOMon(object):
    def __init__(self):
        self.plugin_name = 'collectd-iostat-python'
        self.iostat_path = '/usr/bin/iostat'
        self.interval = 60.0
        self.iostat_interval = 2
        self.iostat_count = 2
        self.iostat_disks = []
        self.iostat_nice_names = False
        self.iostat_disks_regex = ''
        self.iostat_udevnameattr = ''
        self.skip_multipath = False
        self.verbose_logging = False
        self.iostat_no_dm_name = False
        self.names = {
            'tps': {'t': 'transfers_per_second'},
            'Blk_read/s': {'t': 'blocks_per_second', 'ti': 'read'},
            'kB_read/s': {'t': 'bytes_per_second', 'ti': 'read', 'm': 1024},
            'MB_read/s': {'t': 'bytes_per_second', 'ti': 'read', 'm': 1048576},
            'Blk_wrtn/s': {'t': 'blocks_per_second', 'ti': 'write'},
            'kB_wrtn/s': {'t': 'bytes_per_second', 'ti': 'write', 'm': 1024},
            'MB_wrtn/s': {'t': 'bytes_per_second', 'ti': 'write', 'm': 1048576},
            'Blk_read': {'t': 'blocks', 'ti': 'read'},
            'kB_read': {'t': 'bytes', 'ti': 'read', 'm': 1024},
            'MB_read': {'t': 'bytes', 'ti': 'read', 'm': 1048576},
            'Blk_wrtn': {'t': 'blocks', 'ti': 'write'},
            'kB_wrtn': {'t': 'bytes', 'ti': 'write', 'm': 1024},
            'MB_wrtn': {'t': 'bytes', 'ti': 'write', 'm': 1048576},
            'rrqm/s': {'t': 'requests_merged_per_second', 'ti': 'read'},
            'wrqm/s': {'t': 'requests_merged_per_second', 'ti': 'write'},
            'r/s': {'t': 'per_second', 'ti': 'read'},
            'w/s': {'t': 'per_second', 'ti': 'write'},
            'rsec/s': {'t': 'sectors_per_second', 'ti': 'read'},
            'rkB/s': {'t': 'bytes_per_second', 'ti': 'read', 'm': 1024},
            'rMB/s': {'t': 'bytes_per_second', 'ti': 'read', 'm': 1048576},
            'wsec/s': {'t': 'sectors_per_second', 'ti': 'write'},
            'wkB/s': {'t': 'bytes_per_second', 'ti': 'write', 'm': 1024},
            'wMB/s': {'t': 'bytes_per_second', 'ti': 'write', 'm': 1048576},
            'avgrq-sz': {'t': 'avg_request_size'},
            'avgqu-sz': {'t': 'avg_request_queue'},
            'await': {'t': 'avg_wait_time'},
            'r_await': {'t': 'avg_wait_time', 'ti': 'read'},
            'w_await': {'t': 'avg_wait_time', 'ti': 'write'},
            'svctm': {'t': 'avg_service_time'},
            '%util': {'t': 'percent', 'ti': 'util'}
        }

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def configure_callback(self, conf):
        """
        Receive configuration block
        """
        for node in conf.children:
            val = str(node.values[0])

            if node.key == 'Path':
                self.iostat_path = val
            elif node.key == 'Interval':
                self.interval = float(val)
            elif node.key == 'IostatInterval':
                self.iostat_interval = int(float(val))
            elif node.key == 'Count':
                self.iostat_count = int(float(val))
            elif node.key == 'Disks':
                self.iostat_disks = val.split(',')
            elif node.key == 'NiceNames':
                self.iostat_nice_names = val in ['True', 'true']
            elif node.key == 'DisksRegex':
                self.iostat_disks_regex = val
            elif node.key == 'UdevNameAttr':
                self.iostat_udevnameattr = val
            elif node.key == 'PluginName':
                self.plugin_name = val
            elif node.key == 'Verbose':
                self.verbose_logging = val in ['True', 'true']
            elif node.key == 'SkipPhysicalMultipath':
                self.skip_multipath = val in [ 'True', 'true' ]
            elif node.key == 'NoDisplayDMName':
                self.iostat_no_dm_name = val in [ 'True', 'true' ]
            else:
                collectd.warning(
                    '%s plugin: Unknown config key: %s.' % (
                        self.plugin_name,
                        node.key))

        self.log_verbose(
            'Configured with iostat=%s, interval=%s, count=%s, disks=%s, '
            'disks_regex=%s udevnameattr=%s skip_multipath=%s no_dm_name=%s' % (
                self.iostat_path,
                self.iostat_interval,
                self.iostat_count,
                self.iostat_disks,
                self.iostat_disks_regex,
                self.iostat_udevnameattr,
                self.skip_multipath,
                self.iostat_no_dm_name))

        collectd.register_read(self.read_callback, self.interval)

    def dispatch_value(self, plugin_instance, val_type, type_instance, value):
        """
        Dispatch a value to collectd
        """
        self.log_verbose(
            'Sending value: %s-%s.%s=%s' % (
                self.plugin_name,
                plugin_instance,
                '-'.join([val_type, type_instance]),
                value))

        val = collectd.Values()
        val.plugin = self.plugin_name
        val.plugin_instance = plugin_instance
        val.type = val_type
        if len(type_instance):
            val.type_instance = type_instance
        val.values = [value, ]
        val.meta={'0': True}
        val.dispatch()

    def read_callback(self):
        """
        Collectd read callback
        """
        self.log_verbose('Read callback called')
        iostat = IOStat(
            path=self.iostat_path,
            interval=self.iostat_interval,
            count=self.iostat_count,
            disks=self.iostat_disks,
            no_dm_name=self.iostat_no_dm_name)
        ds = iostat.get_diskstats()

        if not ds:
            self.log_verbose('%s plugin: No info received.' % self.plugin_name)
            return

        if self.iostat_udevnameattr and pyudev_available:
            context = pyudev.Context()

        for disk in ds:
            if not re.match(self.iostat_disks_regex, disk):
                continue
            if self.iostat_udevnameattr and pyudev_available:
                device = pyudev.Device.from_device_file(context, "/dev/" + disk)
                if self.skip_multipath:
                    mp_managed = device.get('DM_MULTIPATH_DEVICE_PATH')
                    if mp_managed and mp_managed == '1':
                        self.log_verbose('Skipping physical multipath disk %s' % disk)
                        continue
                if self.iostat_udevnameattr:
                    persistent_name = device.get(self.iostat_udevnameattr)
                    if not persistent_name:
                        self.log_verbose('Unable to determine disk name based on UdevNameAttr: %s' % self.iostat_udevnameattr)
                        persistent_name = disk
            else:
                persistent_name = disk

            for name in ds[disk]:
                if self.iostat_nice_names and name in self.names:
                    val_type = self.names[name]['t']

                    if 'ti' in self.names[name]:
                        type_instance = self.names[name]['ti']
                    else:
                        type_instance = ''

                    value = ds[disk][name]
                    if 'm' in self.names[name]:
                        value *= self.names[name]['m']
                else:
                    val_type = 'gauge'
                    tbl = string.maketrans('/-%', '___')
                    type_instance = name.translate(tbl)
                    value = ds[disk][name]
                self.dispatch_value(
                    persistent_name, val_type, type_instance, value)

def restore_sigchld():
    """
    Restore SIGCHLD handler for python <= v2.6
    It will BREAK exec plugin!!!
    See https://github.com/deniszh/collectd-iostat-python/issues/2 for details
    """
    if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)


if __name__ == '__main__':
    iostat = IOStat()
    ds = iostat.get_diskstats()

    for disk in ds:
        for metric in ds[disk]:
            tbl = string.maketrans('/-%', '___')
            metric_name = metric.translate(tbl)
            print("%s.%s:%s" % (disk, metric_name, ds[disk][metric]))

    sys.exit(0)
else:
    import collectd

    iomon = IOMon()

    # Register callbacks
    collectd.register_init(restore_sigchld)
    collectd.register_config(iomon.configure_callback)
