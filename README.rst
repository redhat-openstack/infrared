=================
InfraRed CLI tool
=================

Reduce users' dependency on external CLI tools (Ansible and others).

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
InfraRed extends the ``clg`` and ``argpars`` packages with the following types
that need to be defined in `.spec` files:

* **Value**: String values
* **YamlFile**: Expects path to YAML files. Will search for files in the settings directory before trying to resolve
  absolute path. For the argument name is "arg-name" and of subparser "SUBCOMMAND" of command "COMMAND", the default
  search path would be::

    settings_dir/COMMAND/SUBCOMMAND/arg/name/arg_value

* **Topology**: Provisioners allow to dynamically define the provisioned
  nodes topology. InfraRed provides several
  'mini' YAML files to describe different roles: ``controller``, ``compute``,
  ``undercloud``, etc...
  These 'mini' files are then merged into one topology file according to the
  provided ``--topology-nodes`` argument value.

  The ``--topology-nodes`` argument can have the following format:
   * ``--topology-nodes=1_controller,1_compute``
   * ``--topology-nodes=1_controller``
   * ``--topology-nodes=3_controller,1_compute,1_undercloud``

 InfraRed will read dynamic topology by following the next steps:
  #. Split the topology value with ','.
  #. Split each node with '_' and get pair (number, role). For every pair
     look for the topology folder (configured in the infrared.cfg file) for
     the appropriate mini file (controller.yml, compute.yml, etc). Load the
     role the defined number of times into the settings.

 .. note:: The default search path for topology files is
       ``settings/provivisioner/topology``. Users can add their own topology
       roles there and reference them on runtime

These arguments will accept input from sources in the following priority
order:

#. Command line arguments:
   ``ir-provision virsh --host-address=some.host.com --host-user=root``
#. Environment variables: ``HOST_ADRRESS=earth.example.com ir-provision virsh --host-user=root``
#. Predefined arguments in ini file specified using ``--from-file`` option::

    ir-provision virsh --host-address=some.host.com --from-file=user.ini

    cat user.ini
    [virsh]
    host-user=root
    host-key=mkey.pm

#. Defaults defined in ``.spec`` file for each argument.

  .. note:: The sample `ini` file with the default values can be generated with:
   ``ir-povision virsh --generate-conf-file=virsh.ini``. Generated file will contain
   all the default arguments values defined in the spec file.

Arguments of the above types will be automatically injected into settings
YAML tree in a nested dict from.

Example:
The input for ``ir-COMMAND`` and argument ``--arg-name=arg-value`` maps to:

  .. code-block:: yaml

      COMMAND:
          arg:
              name: "arg-value"

"arg-value" can be a simple string or be resolved into a more advanced
dictionary depending on the argument type in ``.spec`` file

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

#. Creating a specification file:
    InfraRed uses ArgParse wrapper module called 'clg' in order to create a parser that based on `spec` file
    (YAML format file) containing the plugin options.
    The spec file should be named as the new plugin name with '.spec' extension and located inside the plugin dir
    under the InfraRed 'setting' dir.
    For more details on how to use this module, please visit the 'clg' module `homepage <http://clg.readthedocs
    .org/en/latest/>`_.

#. Creating settings files.
    Settings files are files containing data which defines how the end result of the playbook execution will be
    looked like. Settings file are file in YAML format, end with ".yml" extension. Those files located under the
    plugin's dir which itself located under the 'settings' dir in the InfraRed project's dir.
    The end result of the playbook execution is based on the data created by merging of several settings files together
    with other values, all are received by the user.
    When adding a new plugin, there is a need to create those settings files containing the needed data for the
    playbook execution.
