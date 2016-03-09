=================
InfraRed CLI tool
=================

Reduce users' dependency on external CLI tools (Ansible and others).

Setup
=====

.. note:: On Fedora 23 `BZ#1103566 <https://bugzilla.redhat.com/show_bug.cgi?id=1103566>`_
 calls for::

  $ dnf install redhat-rpm-config

Use pip to install from source::

  $ pip install <path_to_infrared_dir>

So, After cloning repo from GitHub::

 $ cd Infrared
 $ pip install .

.. note:: For development work it's better to install in editable mode::

  $ pip install -e .

Conf
====

``infrared`` will look for ``infrared.cfg`` in the following order:

#. In working directory: ``./infrared.cfg``
#. In user home directory: ``~/.infrared.cfg``
#. In system settings: ``/etc/infrared/infrared.cfg``

.. note:: To specify a different directory or different filename, override the
 lookup order with ``IR_CONFIG`` environment variable::

    $ IR_CONFIG=/my/config/file.ini ir-provision --help

Running InfraRed
================

InfraRed has several "entry points". Currently available: [``ir-provision``]

You can get general usage information with the ``--help`` option::

  ir-provision --help

This displays options you can pass to ``ir-provision``, as well as plugins available as "subcommands"::

  $ ir-provision --help
  usage: ir-provision [-h] [-v] {virsh} ...

  positional arguments:
    {virsh}
      virsh               Provision systems using 'virsh'


External setting trees
======================
InfraRed builds settings tree (YAML dict-like structures) that are later passed to Ansible
as varibales. This tree can be built upon pre-existing YAML files (with ``-i``/``--input``) ,
or be overridden post creation by other pre-existing files and/or sets of ``key=value`` arguments.

The merging priority order is:

1. Input files
2. Settings dir based options
3. Extra Vars



InfraRed input arguments
------------------------
InfraRed accepts the next sources of the input arguments (in priority order):

#. Command line arguments:  ``ir-provision virsh --host=some.host.com --ssh_user=root``
#. Predefined arguments in ini file. Use the --from-file option to specify ini file:

  ```
  $ ir-provision virsh --host=some.host.com --from-file=user.ini
  $ cat user.ini
  [virsh]
  ssh_user=root
  ssh_key=mkey.pm
  ```

#. Environment variables: ``HOST=earth ir-provision virsh --ssh_user=root``

Command line arguments have the highest priority. All the undefined variables will be replaced by that arguments from file or from environment.

Extra-Vars
----------
Set/overwrite settings in the output file using the '-e/--extra-vars'
option. There are 2 ways of doing so:

1. Specific settings: (``key=value`` form)
    ``-e provisioner.site.user=a_user``
2. Path to a settings file: (starts with ``@``)
    ``-e @path/to/a/settings_file.yml``

The ``-e``/``--extra-vars`` can be used more than once.


Add new Plugins
===============

There are two steps that should be done when adding a new plugin to InfraRed:

1. Creating a specification file:
    InfraRed uses ArgParse wrapper module called 'clg' in order to create a parser that based on `spec` file
    (YAML format file) containing the plugin options.
    The spec file should be named as the new plugin name with '.spec' extension and located inside the plugin dir
    under the InfraRed 'setting' dir.
    For more details on how to use this module, please visit the 'clg' module `homepage <http://clg.readthedocs
    .org/en/latest/>`_.

2. Creating settings files.
    Settings files are files containing data which defines how the end result of the playbook execution will be
    looked like. Settings file are file in YAML format, end with ".yml" extension. Those files located under the
    plugin's dir which itself located under the 'settings' dir in the InfraRed project's dir.
    The end result of the playbook execution is based on the data created by merging of several settings files together
    with other values, all are received by the user.
    When adding a new plugin, there is a need to create those settings files containing the needed data for the
    playbook execution.
