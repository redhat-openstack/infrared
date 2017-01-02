.. highlight:: plain

Collect-logs
============
Collect-logs plugin allows the user to collect files & dirs from all inventory hosts in the active profile into a given directory.
List of paths to be archived is gathered from all executed plugins and stored as a YAML file in the active profile dir in a file named ``.archive``.
Logs are being packed as ``tar.gz`` files by default, unless the user explicitly use the ``--gzip`` flag that will instruct the plugin to compress the logs in ``gzip`` format.

.. note:: A user can manually delete/modify the ``.archive`` in the profile's directory, or by running ``infrared profile cleanup`` command.

Each plugin may define a list of files/directories to be archived in a list named ``archive`` on the top level of its spec file.
Example:

.. code:: bash
   :name: spec-with-archive-list

   $ cat plugin_dir/plugin.spec
     plugin_type: sample_plugin
     description: description for sample_plugin
     archive:
         - /home/user/
         - /var/log/
     subparsers:
         sample_plugin:
             help: Help for sample_plugin

Usage example:

.. code:: text
   :name: collect-logs-exe

   $ ir collect-logs --dest-dir=/tmp/ir_logs
