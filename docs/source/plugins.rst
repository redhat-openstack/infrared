Plugins
=======

In InfraRed 2.0, `plugins` are fully self contained Ansible projects.
Any ansible project can become an InfraRed plugin by adhering to the following
structure (see ``tests/example`` for an example plugin)::

    tests/example
    ├── main.yml                # Main playbook. All execution starts here
    └── plugin.spec             # Plugin definition


Add:
    InfraRed will look for a `plugin.spec <Specification>`_ file in the given directory and
    register the plugin under the given plugin-type::

        infrared plugin add tests/example

.. note:: Supported plugin types are defined in plugin settings file which is auto generated and can be found in ``infrared.cfg``.

List:
    List all available plugins, by type::

        infrared plugin list

        Available plugins:
          provision       {example}
          install         {}
          test            {}

Remove:
    Remove an exisitng plugin::

        infrared plugin remove provision example

Execute:
    Plugins are added as subparsers under ``plugin type`` and will execute
    the ``main.yml`` `playbook <playbooks>`_::

        infrared example


Specification
-------------
InfraRed gets all plugin info from ``plugin.spec`` file. Following `YAML` format.
This file define the CLI this plugin exposes, its name and its type.

.. literalinclude:: ../../tests/example/plugin.spec

Playbooks
---------
InfraRed will look for a playbook called ``main.yml`` to start the execution from.

