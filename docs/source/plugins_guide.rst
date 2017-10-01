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
    * ``main.yml``: the entry point anbile playbook which will be run by the Infrared


Create plugin.spec
==================
The ``plugin.spec`` holds the descriptions of all the CLI flags as well as plugin name and plugin descriptions.
Sample plugin specification file can be like::

    plugin_type: other
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
                      flag:
                          type: Bool
                          default: False



Options::
    * ``plugin_type``: plugin type
        Depending of what plugin is intended to do, can be ``provision``, ``install``, ``test`` or ``other``.
        See `plugin specification`_ for details.
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
Infrared collects user input from command line and pass it to the ansible by calling ``main.yml`` playbook.

The ``main.yml`` is the regular ansible playbook and can look like::

    - hosts: localhost
      tasks:
          - name: debug user variables
            debug:
                var: other.option

          - name: check bool flag
            debug:
                msg: "User flag is set"
            when: other.flag


All the options provided by user goes to the plugin type namespace. Dashes in option names translated to the dots (``.``).
So for ``--option1 bar`` infrared will create the ``other.option1: bar`` ansible variable.

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


Using an exiting Ansible project/role as InfraRed plugin
--------------------------------------------------------

InfraRed allows work with an existing Ansible's project/role as an InfraRed plugin.
This will save users from the need to create their own copy of the code and to fetch changes from one repo to the other in order to stay updated.
It also eliminate intervention in project belonging to someone else by saving the need to add the 'plugin.spec' & 'main.yaml' file into them.

Users will need to create those two files ('plugin.spec' & 'main.yml') in a local or remote location, and to point into the remote Ansible role/project in the spec file.
The 'main.yml' will have to call the role/project entry playbook.

An example of a 'plugin.spec' file with multiple remotes::

    ---
    plugin_type: other
    remotes:
        - name: ansible_project
          url: https://my.git.com/user_account/ansible_project.git
        - name: ansible_role
          url: https://my.git.com/user_account/ansible_role.git
          dest_dir: roles/my_role
    subparsers:
        plugin_with_remotes:
            description: A plugin with remotes
            include_groups: []

In the example above, there is a use in two remotes, a project and a role.
When one will add the path / git URL of the (base) plugin which holds this 'plugin.spec' file using the ``infrared plugin add <PLUGIN>`` command,
InfraRed will also clone all of its remotes.
All remotes should be mentioned in the root level of the 'plugin.spec' file like in the example above.
The value of the 'remotes' key is a list of one or more remotes, while each element holds an information on its remote.
The 'name' & 'url' are two mandatory keys for each element in the list, and they tell the name and the URL of each remote respectively.

.. note:: The 'dest_dir' key points to the directory where to clone the remote. If not given, it'll be cloned into a directory with the same name as the remote, inside the base plugin directory.


After creating the 'plugin.spec' file with its remotes, we can now create the 'main.yml' file that will make a use in the just cloned remotes.

An example of a 'main.yml' with use in remotes::

    ---
    - name: Ansible project
      include: ansible_project/playbook.yml

    - name: Ansible role
      hosts: localhost
      roles:
        - my_role

In the first and second tasks of the playbook above, there is a call to the entry playbook in the Ansible project and role we just cloned.