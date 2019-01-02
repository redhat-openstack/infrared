How to create a new plugin
--------------------------

This is a short guide how new plugin can be added to the Infrared.
It is recommended to read `Plugins`_ section prior following steps from that guide.

.. _plugins: plugins.html

Create new Git repo for a plugin
================================

Recommended way to store Infarerd plugin is to put it into a separate Git repo.
So create and init new repo::

    $ mkdir simple-plugin && cd simple-plugin
    $ git init


Now you need to add two main files of every Infrared plugin:
    * ``plugin.spec``: describes the user interface of the plugin (CLI)
    * ``main.yml``: the default entry point anbile playbook which will be run by the Infrared


Create plugin.spec
==================

The ``plugin.spec`` holds the descriptions of all the CLI flags as well as plugin name and plugin descriptions.
Sample plugin specification file can be like::

    config:
       plugin_type: other
       entry_point: main.yml
    subparsers:
        # the actual name of the plugin
        simple-plugin:
            description: This is a simple demo plugin
            include_groups: ["Ansible options", "Common options"]
            groups:
                - title: Option group.
                  options:
                      option1:
                          type: Value
                          help: Simple option with default value
                          default: foo
                          ansible_variable: "myvar"
                      flag:
                          type: Bool
                          default: False

Config section:
    * ``plugin_type``:
        Depending of what plugin is intended to do, can be ``provision``, ``install``, ``test`` or ``other``.
        See `plugin specification`_ for details.
    * ``entry_point``:
        The main playbook for the plugin. by default this will refer to main.yml file
        but can be changed to ant other file.
Options::
    * ``plugin name`` under the ``subparsers``
        Infrared extends it CLI with that name.
        It is recommended to use ``dash-separated-lowercase-words`` for plugin names.
    * ``include_groups``: list what standard flags should be included to the plugin CLI.
        Usually we include "Ansible options" to provide ansible specific options and "Common Options" to
        get ``--extra-vars``, ``--output`` and ``--dry-run``. See `plugins include groups`_ for more information.
    * ``groups``: the list of options groups
        Groups several logically connected options.
    * ``options``: the list of options in a group.
        Infrared allows to define different types of options, set option default
        value, mark options as required etc. Check the `plugins option types`_ for details

.. _plugin specification: plugins.html#plugin-specification
.. _plugins include groups: plugins.html#include-groups
.. _plugins option types: plugins.html#complex-option-types

Create main playbook
====================

Now when plugin specification is ready we need to put some business logic into a plugin.
Infrared collects user input from command line and pass it to the ansible by calling main
playbook - that is configured as entry_point in ``plugins.spec``.

The main playbook is a regular ansible playbook and can look like::

    - hosts: localhost
      tasks:
          - name: debug user variables
            debug:
                var: other.option

          - name: check bool flag
            debug:
                msg: "User flag is set"
            when: other.flag


By default, all the options provided by user goes to the plugin type namespace. Dashes in option names translated to the dots (``.``).
So for ``--option1 bar`` infrared will create the ``other.option1: bar`` ansible variable.

It's possible to assign a user defined ansible variable to an option by specifying ``ansible_variable`` in plugin.spec(refer to ``plugin.spec`` sample).

Push changes to the remote repo
===============================

Commit all the files::

    $ git add .
    $ git commit -m "Initial commit"


Add the URL to the remote repo (for example a GitHub repo) and push all the changes::

    $ git remote add origin <remote repository>
    $ git push origin master



Add plugin to the infrared
==========================

Now you are ready to install and use your plugin.
Install infrared and add plugin by providing url to your plugin repo::

    $ ir plugin add <remote repo>
    $ ir plugin list

This should display the list of plugins and you should have your plugin name there::

    ┌───────────┬────────────────────┐
    │ Type      │ Name               │
    ├───────────┼────────────────────┤
    │ provision │ beaker             │
    │           │ virsh              │
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ├───────────┼────────────────────┤
    │ other     │ simple-plugin      │
    │           │ collect-logs       │
    └───────────┴────────────────────┘



Run plugin
==========

Run plugin with infrared and check for the help message::

    $ ir simple-plugin --help

You should see user defined option as well as the common options like --extra-args.

Run ir command and check the playbook output::

    $ ir simple-plugin --options1 HW  --flag yes

