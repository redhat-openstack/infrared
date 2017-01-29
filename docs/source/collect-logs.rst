.. highlight:: plain

Collect-logs
============
Collect-logs plugin allows the user to collect files & dirs from hosts
managed by active workspace. A list of paths to be archived is taken from
``vars/default_archives_list.yml`` in the plugin's dir. Logs are being
packed as ``.tar`` files by default, unless the user explicitly use the
``--gzip`` flag that will instruct the plugin to compress the logs with ``gzip``.

.. note:: All nodes must have yum repositories configured in order for the tasks to work on them.

.. note:: Users can manually modify the ``default_archives_list.yml`` if need to add/delete paths.

Usage example::

    ir collect-logs --dest-dir=/tmp/ir_logs
