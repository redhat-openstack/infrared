.. highlight:: text

Collect-logs
============
Collect-logs plugin allows the user to collect files & directories from hosts
managed by active workspace. A list of paths to be archived is taken from
``vars/default_archives_list.yml`` in the plugin's dir. Logs are being
packed as ``.tar`` files by default, unless the user explicitly use the
``--gzip`` flag that will instruct the plugin to compress the logs with ``gzip``.
Also it supports 'sosreport_' tool to collect configuration and diagnostic information
from system. It is possible to use both logger facilities, log files from the host and
sosreport.

.. _sosreport: https://access.redhat.com/solutions/3592

.. note:: All nodes must have yum repositories configured in order for the tasks to work on them.

.. note:: Users can manually edit the ``default_archives_list.yml`` if need to add/delete paths.

.. note:: All nodes must have yum repositories configured in order for the tasks to work on them.

.. note:: To enable logging using all available faclilties, i.e. host and sosreport use parameter --logger=all


Usage example::

    ir collect-logs --dest-dir=/tmp/ir_logs

    ir collect-logs --dest-dir=/tmp/ir_logs --logger=sosreport
