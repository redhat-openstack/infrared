.. include:: warning.txt

.. highlight:: plain

Specifications
==============

InfraRed "drives" Ansible through a Plugin's playbooks (and roles) in the following manner::

  ir-XXXer YYYer [...]

Where ``XXX`` is the `command` (``provision``, ``install``, or ``test``), and ``YYY`` is the plugin `subcommand` (``virsh``, ``ospd``, ``openstack``, ``tempest``, etc...)

* Each `command` executes a matching playbook (at ``playbooks/XXX.yml``) with a generated set of `extra vars <http://docs.ansible.com/ansible/playbooks_variables.html#passing-variables-on-the-command-line>`_
  as `plugin input`_.
* That "top" playbook calls (via "include") to the `subcommand`'s playbook at ``playbooks/XXXer/YYY.yml``

Plugin Input
------------

InfraRed exposes several types of arguments via it's CLI to accept user-input before execution.
It generates a python-dict input and merges it with a dict of defaults defined in YAML format.

If the `subcommand` is called ``YYY``, InfraRed will search for its input definitions in `settings trees <setup.html#private-settings>`_
in a directory called ``YYY``.

Infrared uses special files (in YAML format) to describe plugin CLI interface.
These files are called *specifications* (spec's) and have ``.spec`` extension.

The main idea of specification is to describe:
    * all the possible options we can pass to the plugin
    * any default values for the options
    * required and optional options
    * limitation for certain options, like choosing option value from the predefined list of allowed values

Infrared parses and merges all the spec files under the settings folders and pass
all the defined options to the ``argparse`` module which is then used for cli options parsing.

Specification parser is derived from 'clg' module `homepage <http://clg.readthedocs.org/en/latest/>`_.


Commands and subcommands
------------------------
Infrared uses the positional arguments (subcommands) to extend functionality
for the ir-* cli commands.

.. code-block:: plain

    ir-provisioner [..] openstack [...]
       ^---------^      ^-------^
         command        subcommand

For example, the provisioner command aggregates several subcommands which define specific provisioners like virsh, openstack, beaker, foreman, etc.

The command specification files are stored under the ``settings/<command_name>/`` folders.

Command specification should start from the root of the spec file without any additional keywords:

.. code-block:: plain

   ---
   options: [....]
   groups:  [....]


All the subcommand specifications files are stored under the ``settings/<command_name>/<subcommand_name>`` folders.


Subcommands can be defined with the ``subparsers`` keyword followed by the subcommand name:

.. code-block:: yaml

    ---
    subparsers:
        virsh:
            options:
            [....]
            groups:
            [....]


It's recommended to define subcommands in the seprate .spec file.


Infrared settings structure
---------------------------

.. code-block:: plain

    [settings]
        |
        +-> [installer]
        |       |
        |       +-> [ospd]
        |       |      |
        |       |      +-> ospd.spec
        |       |      |
        |       |      +-> ospd.yml
        |       |
        |       +-> [packstack]
        |       |      |
        |       |      +-> packstack.spec
        |       |      |
        |       |      +-> packstack.yml
        |       |
        |       +-> installer.spec
        |
        +-> [provisioner]
        |       |
        |       +-> [....]
        |       |
        |       +-> provisioner.spec
        |       |
        |       +-> provisioner.yml
        |
        +-> base.spec

The ``base.spec`` file contains:
    * groups and options common for all the commands
    * reusable groups (shared_groups)

The command specification files ``installer/installer.spec`` and ``provisioner/provisioner.spec`` contain:
    * specific options and groups for a given command. For example, by default ir-provisioner command has the --debug flag to debug information into console.

The subcommand specification files ``installer/ospd/ospd.spec`` and ``installer/ospd/packstack.spec`` contain:
    * subcommand name and description
    * specific options and groups for a given subcommand

The subcommand default files ``installer/ospd/ospd.yml`` and ``installer/ospd/packstack.yml`` contain:
    * A set of `extra vars <http://docs.ansible.com/ansible/playbooks_variables.html#passing-variables-on-the-command-line>`_ in YAML format
      which the subcommand will use as the skeleton for its input


Options and Groups
------------------

An option can be defined with an ``options`` keyword followed by the dict of options. Every key in that dict is an option name, and value is another dict of option parameters.

.. code-block:: yaml

    ---
    options:
        debug:
            help: Run InfraRed in DEBUG mode
            short: d
            action: store_true

        verbose:
            help: Control Ansible verbosity level
            short: v
            action: count
            default: 0


Infrared transforms that to the CLI tool with the following arguments:

.. code-block:: bash

    ir-command [-h] [-d] [-v]

    optional arguments:
    -h, --help            show this help message and exit
    -d, --debug           Run InfraRed in DEBUG mode
    -v, --verbose         Control Ansible verbosity level


Options configuration
*********************

Every option in the specification can have the following keywords:

    * `short` (``infrared``)
    * `help` (``argparse``)
    * `required` (``argparse``)
    * `default` (``argparse``)
    * `choices` (``argparse``)
    * `action` (``argparse``)
    * `nargs` (``argparse``)
    * `const` (``argparse``)
    * `type` (``argparse``)
    * `silent` (``infrared``)
    * `required_when` (``infrared``)

short
~~~~~
This section must contain a single letter defining the short name (beginning
with a single dash) of the current option.


help
~~~~
**argparse link**: `<https://docs.python.org/dev/library/argparse.html#help>`_

A brief description of what the argument does.


required
~~~~~~~~
**argparse link**: `<https://docs.python.org/dev/library/argparse.html#required>`_

Whether or not the command-line option may be omitted.


type
~~~~
**argparse link**: `<https://docs.python.org/dev/library/argparse.html#type>`_

The type to which the command-line argument should be converted.

There are two groups of type supported by Infrared:
    * control types: all the builtin types such as 'str', 'int' and other. Option with these types are used to control Infrared behavior and will not be put into the generated settings files. For example, ir-provisioner command has 'debug' control option.
    * settings types (Value types): ``Value``, ``YamlFile``, ``Topology`` and other types. Options with these types will be put by Infrared into the settings files.

If type is not specified, Infrared will treat such option as 'str' control option.


Settings types
''''''''''''''

    * `Value`_
    * `YamlFile`_
    * `ListOfYamls`_
    * `Topology`_
    * `DictValue`_

Value
"""""

Simple value which will be put into the command settings. For example if for 'provisioner' command and the 'virsh' subcommand with options:

.. code-block:: yaml

   ---
   subparsers:
       virsh:
           options:
               host-address:
                   type: Value
                   help: 'Address/FQDN of the BM hypervisor'
                   required: yes


Calling the 'ir-provisioner' cli tool::

    ir-provisioner virsh --host-address myhost.domain.com


will produce the folloiwng settings in YAML format:

.. code-block:: yaml

   ---
   provisioner
       host:
           address: myhost.domain.com

This settings tree is passed to Ansible as extra-vars.


YamlFile
""""""""

Loads the content of the specified YAML file into the settings.
For the option named 'arg-name' Infrared will look for YAML file into the following locations:

    #. <settings folder>/<command name>/<subcommand name>/arg/name/<file_name>
    #. <settings folder>/<command name>/arg/name/<file_name>
    #. ./arg/name/<file_name>

For example, the 'provisioner' command and virsh 'subcommand' has the YamlFile option:

.. code-block:: yaml

   ---
   subparsers:
       virsh:
           options:
               topology-network:
                   type: YamlFile
       ....


Command call::

   ir-provisioner virsh --topology-network=default.yml


Infrared will look for `default.yml` in the following locations:
   #. settings/provisioner/virsh/topology/network/default.yml
   #. settings/provisioner/topology/network/default.yml
   #. ./topology/network/default.yml

Content of the `default.yml` will be put into the settings file:

.. code-block:: yaml

   ---
   provisioner:
       topology:
           network:
               # content of the default.yml will go there
               key1: value
               key2: value
               ....


Topology
""""""""

Topology type is used to describe what nodes (vm's) should be provisioned by the provisioner.

Topology value should be the list of nodes names and the number of nodes: ``<node name>:<node number>,<node2 name>:<node2 number>,...``. For example:

.. code-block::  bash

   ir-provisioner virsh --topology-nodes=undercloud:1,controller:2,compute:3
   ir-provisioner virsh --topology-nodes=controller:3


Every node name maps to the appropriate YAML file (undercloud.yml. controller.yml, controller.yml) that should be stored in one the following locations:

    #. <settings folder>/<command name>/<subcommand name>/arg/name/<file_name>
    #. <settings folder>/<command name>/arg/name/<file_name>
    #. <settings folder>/<command name>/topology/<file_name>
    #. ./arg/name/<file_name>

All the YAML files will be loaded into the settings under the node name key. 'Amount' key will be adjusted.

For example, for ``undercloud:1,controller:2,compute:3`` value with option name ``topology-nodes`` the settings file will be:

.. code-block:: yaml

   ---
   provisioner:
       topology:
           nodes:
               undercloud:
                   # content of the undercloud.yml will go there
                   amount: 1
                controller:
                   # content of the controller.yml will go there
                   amount: 2
                compute:
                   # content of the compute.yml will go there
                   amount: 3

ListOfYamls
"""""""""""

Specifies the list of YAML files to load into the settings.

Option value should be the comma separated string of files to load with or without yml extension. Single element in list is also accepted.

Values examples:
    * item1,item2,item3
    * item1.yml

Search locations are the same as for the ``YamlFile`` type.

For example, for ``network,compute,volume`` value with option name ``tests``, command ``tester`` and subcommand ``tempest``, the settings file will be:

.. code-block:: yaml

   ---
   tester:
       tests:
           network:
               # content of the network.yml will go there

           compute:
               # content of the compute.yml will go there

           volume:
               # content of the volume.yml will go there

DictValue
"""""""""

Specifies the value which should be interpreted as a dictionary value in the settings.

DictValue should be specified in the format: ``option1=value1;option2=value;option3=value3``

Consider the following example on how to add the DictValue option into a spec.

.. code-block:: yaml

   ---
   subparsers:
       virsh:
           options:
               my-dict-option:
                   type: DictValue
                   help: 'Sample dict'


Calling the cli tool::

    ir-provisioner virsh --my-dict-option=option1=value1;key2=value2


will produce the following dict tree in YAML format:

.. code-block:: yaml

   ---
   provisioner
       my:
           dict:
               options:
                   option1: value1
                   key2: value2

This settings tree is passed to Ansible as extra-vars.


Types extension
'''''''''''''''

Settings types can be extended by adding user class to the ``clg.COMPLEX_TYPES dictionary``. Complex types should implement the ``clg.ComplexType`` interface:

.. code-block:: python

    import clg
    from datetime import datetime

    class DateValue(ComplexType):

        def resolve(self, value):
            try:
                return datetime.strptime(value, '%d/%m/%Y')
            except Exception as err:
                raise clg.argparse.ArgumentTypeError(err)

    COMPLEX_TYPES['DateValue'] = DateValue

    # proceed with clg usage
    ...


YAML configuration is then can look like:

.. code-block:: yaml

    ---
    options:
        date:
            help: Date value
            type: DateValue
    ...


Control types can be extended by adding callable objects which accept one
argument (value) to the ``clg.TYPES`` dictionary.



default
~~~~~~~
**argparse link**: `<https://docs.python.org/dev/library/argparse.html#default>`_

The value produced if the argument is absent from the command line.


choices
~~~~~~~
**argparse link**: `<https://docs.python.org/dev/library/argparse.html#choices>`_

A container of the allowable values for the argument.


action
~~~~~~
**argparse link**: `<https://docs.python.org/dev/library/argparse.html#action>`_

The basic type of action to be taken when this argument is encountered at the
command line.

Infrared provides two actions which allows to read options from INI files and generate simple configuration files.

.. code-block:: yaml

    ---
    options:
        from-file:
            action: read-config
            help: reads arguments from file.
        generate-conf-file:
            action: generate-config
            help: generate configuration file with default values


nargs
~~~~~
**argparse link**: `<https://docs.python.org/dev/library/argparse.html#nargs>`_

The number of command-line arguments that should be consumed.


const
~~~~~
**argparse link**: `<https://docs.python.org/dev/library/argparse.html#const>`_

Value in the resulted `Namespace` if the option is not set in the command-line
(*None* by default).

silent
~~~~~~

Specifies which required arguments should become no longer required when this option is set.

.. code-block:: yaml

    ---
    options:
        image:
            type: YamlFile
            help: 'The image to use for nodes provisioning. Check the "sample.yml.example" for example.'
            required: yes
        ...
        cleanup:
            action: store_true
            help: Clean given system instead of running playbooks on a new one.
            silent:
                - "image"
    ...

In that example the image will no longer be required when cleanup option is set.


required_when
~~~~~~~~~~~~~

Specifies condition when options should became required.

Condition should be specified in form *<option_name> == <value>*.

.. code-block:: yaml

    ---
    options:
        images-task:
            type: Value
            choices: [import, build, rpm]
            default: rpm

        images-url:
            type: Value
            help: Specifies the import image url. Required only when images task is 'import'
            required_when: "images-task == import"


Groups
******

If options belong to one area or connected somehow, they can be grouped:

.. code-block:: yaml

    ---
    groups:
        - title: Hypervisor
          options:
              host-address:
                  type: Value
                  help: 'Address/FQDN of the BM hypervisor'
                  required: yes
              host-user:
                  type: Value
                  help: 'User to SSH to the host with'
                  default: root
              host-key:
                  type: Value
                  help: "User's SSH key"
                  required: yes


Shared groups
*************

Shared groups allow to include predefined options groups into different commands or subcommands

Shared groups should be defined in the ``settings/base.spec`` file or in the command spec file:

.. code-block:: yaml

    ---
    shared_groups:
        - title: Inventory hosts options
          options:
            inventory:
                help: Inventory file
                type: str
                default: hosts

        - title: Common options
          options:
            dry-run:
                action: store_true
                help: Only generate settings, skip the playbook execution stage
            input:
                action: append
                type: str
                short: i
                help: Input settings file to be loaded before the merging of user args


Shared group can be included into the **command** spec file with the ``include_groups`` directive:

.. code-block:: yaml

    ---
    include_groups: ["Debug Options"]


For a **subcommand** the ``include_groups`` should be defined under the subparsers section:

.. code-block:: yaml

    ---
    subparsers:
        virsh:
            include_groups: ["Ansible options", "Inventory options", "Common options", "Configuration file options"]


Options sources
***************

Infrared is not limited with the CLI options only.
We can pass arguments to the plugin using the following approaches:
    * through the CLI options
    * through INI files using the ``--from-file`` argument or any other argument with  ``action: read-config`` attribute in specification
    * through environment variables


Infrared resolves option value in the next order:
    #. If option value is provided by CLI, use that value.
    #. Else use value from INI file if it is defined there.
    #. Else use environment variable (with the same name as an option name, but capitalized and '-' replaced with '_' (for example, 'arg-name' will be transformed to ARG_NAME env variable).
    #. Else use value specified by the default keyword in the spec file.
    #. If default value is not specified, option will not be defined.

Consider the following subcommand specification as an example:


.. code-block:: yaml

    ---
    subparsers:
        testcommand:
            groups:
                - title: common options
                  options:
                      from-file:
                          action: read-config
                          help: reads arguments from file.


                - title: test options
                  options:
                      option1:
                          type: Value
                      option2:
                          type: Value
                      option3:
                          type: Value


The INI file with the settings:

.. code-block:: ini

    [testcommand]
    option1=ini_value1
    option2=ini_value2


Invoke subcommand with the following options::

    OPTION2=env_value2 OPTION3=env_value3 ir-somecomand testcommand --from-file=test.ini --option1=cli_value1

This will produce the follwing arguments:
    * option1 = cli_value1
    * option2 = ini_value2
    * option3 = env_value3
