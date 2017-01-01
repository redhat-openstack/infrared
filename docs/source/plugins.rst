Plugins
=======

In InfraRed 2.0, `plugins` are fully self contained Ansible projects.
Any ansible project can become an InfraRed plugin by adhering to the following
structure (see ``tests/example`` for an example plugin)::

    tests/example
    ├── main.yml                # Main playbook. All execution starts here
    ├── plugin.spec             # Plugin definition
    ├── callback_plugins        # Useful to format Ansible console output
    │   ├── human_log.py
    │   ├── timing.py
    ├── filter_plugins          # Add here custom jinja2 filters
    │   └── myfilter.py
    ├── roles                   # Add here roles for the project to use
    │   └── example_role
    │       └── tasks
    │           └── main.yml
    └── vars                    # Add here variable files

.. note:: This structure will work without any ``ansible.cfg`` file provided, as Ansible will search for references in the
        relative paths described above. To use an ``ansible.cfg`` config file, use absolute paths to the plugin directory.

Plugin structure
^^^^^^^^^^^^^^^^

Playbooks
---------
InfraRed will look for a playbook called ``main.yml`` to start the execution from.

Plugins are regular Ansible projects, and as such, they might include or reference any item
(files, roles, var files, ansible plugins, modules, templates, etc...) using relative paths
to current playbook

.. literalinclude:: ../../tests/example/main.yml
   :emphasize-lines: 3-6
   :linenos:

.. note:: the vars-dict defined by `Complex option types`_ is nested under ``plugin_type`` root key, and passed
 to Ansible using ``--extra-vars`` meaning that any vars file that has ``plugin_type`` as a root key, will be
 overriden by that vars-dict. See `Ansible variable precidence`_ for more details.

.. _Ansible variable precidence: http://docs.ansible.com/ansible/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable

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
    * ``--dry-run``: Don't execute Ansible playbook. Only write generated vars dict to stdout
    * ``--output``: Redirect generated vars dict from stdout to an explicit file (YAML format).

Inventory:
    Load a new inventory to active `profile <profile.html>`_. The file is copied to
    profile directory so all ``{{ inventory_dir }}`` references in playbooks still point to
    profile directory (and not to the input file's directory).

    .. note:: This file permenantly becomes the profile's inventory. To revert to original profile
        the profile must be cleaned.

Ansible options:
    * ``--verbose``: Set ansible verbosity level
    * ``--ansible-args``: Pass all subsequent input to Ansible as raw arguments. This is for power-users wishing to access
      Ansible functionality not exposed by `Infrared`::

         infrared [...] --ansible-args step;tags=tag1,tag2;forks=500

      Is the equivalent of::

         ansible-playbook [...] --step --tags=tag1,tag2 --forks 500

Complex option types
~~~~~~~~~~~~~~~~~~~~
`InfraRed` extends `argparse <https://docs.python.org/2/library/argparse.html>`_ with the following option types.
These options are nested into the vars dict that is later passed to Ansible as extra-vars.

* Value:
    Regular string value.
* Bool:
    Boolean value. Accepts any form of YAML boolean: ``yes``/``no``, ``true``/``false`` ``on``/``off``.
    Will fail if the string can't be resolved to this type.
* KeyValueList:
    String representation of a flat dict ``--options option1:value1,option2:value2``
    becomes:

        .. code:: json
           :name: KeyValueList

            {"options": {"option1": "value1",
                         "option2": "value2"}}

    .. note:: | Input value in 'equal-semicolon' (old) format are acceptable but deprecated. It's recommended to use the 'colon-comma' (new) format as shown in the example above.
              | 'equal-semicolon' input example: ``--options option1=value1;option2=value2``

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


Plugin Manager
^^^^^^^^^^^^^^

The following commands are used to manage `InfraRed` plugins

Add:
    InfraRed will look for a `plugin.spec <Specification>`_ file in the given directory and
    register the plugin under the given plugin-type::

        infrared plugin add tests/example


List:
    List all available plugins, by type::

        infrared plugin list

        Available plugins:
          provision       {example}
          install         {}
          test            {}

.. note:: Supported plugin types are defined in plugin settings file which is auto generated and can be found in ``infrared.cfg``.

Remove:
    Remove an exisitng plugin::

        infrared plugin remove provision example

Execute:
    Plugins are added as subparsers under ``plugin type`` and will execute
    the ``main.yml`` `playbook <playbooks>`_::

        infrared example


