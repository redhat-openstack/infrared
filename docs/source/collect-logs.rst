.. highlight:: plain

Collect-logs
============
Collect-logs plugin allows the user to collect files & dirs from all inventory hosts in the active profile into a given directory.
List of paths to be archived is taken from ``vars/default_archives_list.yml`` in the plugin's dir.
Logs are being packed as ``.tar`` files by default, unless the user explicitly use the ``--gzip`` flag that will instruct the plugin to compress the logs in ``gzip`` format.

.. note:: Users can manually modify the ``default_archives_list.yml`` if need to add/delete paths.

Usage example::

    ir collect-logs --dest-dir=/tmp/ir_logs
