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

Include Groups
~~~~~~~~~~~~~~
A plugin can reference preset control arguments to be included in its CLI

Answers File:
    Instead of explicitly listing all CLI options every time, `InfraRed` plugins
    can read their input from ``INI`` answers file, using ``--from-file`` switch.
    use ``--generate-answers-file`` switch to generate such file. It will list all
    input arguments a plugin accepts, with their help and defaults.
    CLI options still take precedence if explicitly listed, even when ``--from-file``
    is used.

Common Options:
    * ``dry-run``: Don't execute Ansible playbook. Only write generated vars dict to stdout
    * ``output``: Redirect generated vars dict from stdout to an explicit file (YAML format).

Complex option types
~~~~~~~~~~~~~~~~~~~~
`InfraRed` extends `argparse <https://docs.python.org/2/library/argparse.html>`_ with the following option types.
These options are nested into the vars dict that is later passed as input to ansible.

* Value: Regular string value.

The nesting is done in the following manner: option name is splited by ``-`` delimiter and each part is
a key of a dict nested in side the previous one, starting with "plugin_type". Then value is nested at the
inner-most level. Example::

    infrared example --foo-bar=value1 --foo-another-bar=value2 --also_foo=value3

.. code:: json
   :name: vars-dict

   {
       "provision": {
           "foo": {
               "bar": "value1",
               "another": {
                   "bar": "value2"
               }
           },
           "also_foo": "value3"
       }
   }

Playbooks
---------
InfraRed will look for a playbook called ``main.yml`` to start the execution from.

