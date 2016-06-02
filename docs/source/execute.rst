.. highlight:: plain

Using InfraRed
================

General workflow
----------------
InfraRed framework is divided into three logically separated (but interconnected) stages (tools):

#. ``ir-provisioner``

#. ``ir-installer``

#. ``ir-tester``

First, create InfraRed config file::

  cp infrared.cfg.example infrared.cfg

.. note:: There is an environment variable called IR_CONFIG that controls the location of the config file (defaults to: ./infrared.cfg). Use if you wish to override local one.

  .. code-block:: plain

    IR_CONFIG=/my/config/file.ini ir-<stage> --help

You can get general usage information with the ``--help`` option::

  ir-<stage> --help

Output will display supported options you can pass to ``ir-<stage>``, as well as available positional arguments for current stage (e.g. for provisioner these are foreman, virsh, openstack, ...):

Also, you can invoke help for specific positional arguments (supported provisioners, in this case)::

  ir-<stage> virsh --help

.. note:: Positional arguments are generated dynamically from spec files - order and amount might change in time.

Passing parameters
^^^^^^^^^^^^^^^^^^
InfraRed expects that selected workflow (playbook and roles) will be provided with all mandatory parameters. There are several ways to do it:

* use `separate private configuration directory <setup.html#private-settings>`_

* include standalone file(s) containing (private) configuration as explicit input file(s) (``-i`` or ``--input`` parameters), for example:

.. code-block:: plain

  ir-<stage> --input private.yml

.. code-block:: plain
   :caption: private.yml

    ---
    private:
       provisioner:
           beaker:
           base_url: "https://beaker_instance_url/"
           username: "..."
           password: "..."
    ...

* or using command line ``ir-<stage> --param1 --param2 ...``

.. note:: Best practice is store infrastructure-specific configuration file(s) in private repository and fetch such file(s) before deployment.

Stage chaining
^^^^^^^^^^^^^^

Provisioners
------------
For list of supported installers invoke::

    $ ir-provisioner -h

Beaker
^^^^^^
Entry point::

  playbooks/provisioner/beaker/main.yml

Beaker provisioner is designed to work with instances of `Beaker project <https://beaker-project.org>`_ at least version 22.3. It is based custom ansible module built on top of

.. code-block:: plain

  library/beaker_provisioner.py

script. Because of not very flexible support of Kerberos in Beaker (with this type of authentication user can not have custom SSH keys set-up, Kerberos handling is not very suitable in dynamic cloud environment), authentication is done using XML-RPC API with credentials for dedicated user.

See appropriate value of ``ssh_pass`` for your ``beaker_username`` in Website -> Account -> Preferences -> Root Passwordf you didn't setup one. For proper XML-RPC calls ``cer_file`` must be provided.

Also, for each run you will need to set proper node-specific values:

.. code-block:: plain

    ...
    Beaker system:
      --fqdn FQDN                Fully qualified domain name of a system
      --distro-tree DISTRO-TREE  Distro Tree ID Default value: 71576
    ...

Foreman
^^^^^^^
Entry point::

  playbooks/provisioner/foreman/cleanup.yml

.. warning:: Currently, Foreman provisioning is not supported. Provision manually and then you can cleanup before every redeployment.

Foreman provisioner is designed to work with instances of `Foreman project <https://theforeman.org>`_ at least version 1.6.3. It is based custom ansible module built on top of

.. code-block:: plain

  library/foreman_provisioner.py

Foreman provisioner expects that provisioned node has configured relevant puppet recipies to provide basic SSH access after provisioning is done.

Openstack
^^^^^^^^^
Entry point::

  playbooks/provisioner/openstack/main.yml

Provisioner is designed to work with existing instances of OpenStack. It is based on native ansible's `cloud modules <http://docs.ansible.com/ansible/list_of_cloud_modules.html#openstack>`_. Workflow can be separated into following stages:

  * Create network infrastructure
  * Create instance of virtual machine and connect to network infrastructure
  * Wait until instance is booted and reachable using SSH

.. note:: Openstack provisioner is tested against Kilo version.

InfraRed interacts with cloud using `os-client-config <http://docs.openstack.org/developer/os-client-config>`_ library. This library expects properly configured cloud.yml file in filesystem, however it is possible to position this file in InfraRed's directory.

.. code-block:: plain
   :caption: clouds.yml

   clouds:
       cloud_name:
           auth_url: http://openstack_instance:5000/v2.0
           username: <username>
           password: <password>
           project_name: <project_name>

``cloud_name`` can be then referenced with ``--cloud`` parameter provided to ``ir-provisioner``::

  ir-provisioner ... --cloud cloud_name ...

Last important parameter is ``--dns`` which must be set to point to local DNS server in your infrastructure.

.. TODO - Why?

Virsh
^^^^^
Virsh provisioner is usually used for setup of virthost topology used to emulate production environment of `OpenStack director <execute.html#id1>`_ instances. It requires prepared baremetal host to be reachable through SSH.

First, Libvirt and KVM environment is installed and configured to provide virtualized environment.  Then, virtual machines are created for all requested nodes. These VM's are used in `OSPd installer <execute.html#id2>`_ as undercloud, overcloud and auxiliary nodes.

Please see `Quickstart <quickstart.html>`_ guide where usage is demonstrated.

.. TODO - Network layout - chapter describing network in detail
Network layout
""""""""""""""
Baremetal machine used as host for such setup is called `virthost`. The whole deployment is designed to work within boundaries of this machine and (except public/natted traffic) shouldn't reach beyond.

.. code-block:: plain

       Virthost
           |
           +--------+ nic0 - public IP
           |
           +--------+ nic1 - not managed
           |
             ...                                         Libvirt VM's (Undercloud, OC nodes)
           |                                                        |
     ------+--------+ data bridge (ctlplane, 192.0.2/24)            +------+ data (nic0)
     |     |                                                        |
 libvirt --+--------+ management bridge (nat, dhcp, 172.16.0/24)    +------+ managementnt (nic1)
     |     |                                                        |
     ------+--------+ external bridge (nat, dhcp, 10.0.0/24)        +------+ external (nic2)

On virthost, there are 3 new bridges created with libvirt - data, management and external. Most important is data network which does not have dhcp and nat enabled. This network is used as ctlplane for OSP director deployments (`OSPd installer <execute.html#id2>`_). Other (usually physical) interfaces are not used (nic0, nic1, ...) except for public/natted traffic.

.. TODO - what other networks do?

Virsh provisioner workflow:

 #. Setup libvirt and kvm environment

 #. Setup libvirt networks

 #. Download base image for undercloud (``--image``)

 #. Create desired amount of images and integrate to libvirt

 #. Define virtual machines with requested parameters (``--topology-nodes``)

 #. Start virtual machines

Environments prepared such way are usually used as basic virtual infrastructure for `OSPd installer <execute.html#OpenStack-director>`_.

Installers
----------
For list of supported installers invoke::

    $ ir-installer -h

Packstack
^^^^^^^^^
Infrared allows to use Packstack installer to install OpenStack::

    $ ir-installer -d -vvvv --inventory hosts packstack --product-version=8 -o install.yml -e @provision.yml

Here required arguments are:
    * ``--product-version`` - the product version to install.

Optional arguments:
    * ``-o provision.yml`` - the settings file generated by provisiner (using ``ir-provisioner [...] -o provision.yml [...]``). It might contain relevant data required for Packstack settings.


Settings structure
""""""""""""""""""

The path for the main settings file for packstack installer::

    settings/installer/packstack/packstack.yml

This file provides defaults settings and default configuration options for the packstack answer files.

Additional answer options can be added using the the following approaches:

    * Using a non default config argument value::

        $ ir-installer --inventory hosts packstack --config=basic_neutron.yml

    * Using the extra-vars flags::

        $ ir-installer --inventory hosts packstack --product-version=8 --extra-vars=installer.config.CONFIG_DEBUG_MODE=no

    * Network based answer file options can be selected whether by choosing network backend or by modyfing config with --extra-vars::

        $ ir-installer --inventory hosts packstack --product-version=8 --network=neutron.yml --netwrok-variant=neutron_gre.yml

        $ ir-installer --inventory hosts packstack --product-version=8 --network=neutron.yml --netwrok-variant=neutron_gre.yml --extra-vars=installer.network.config.CONFIG_NEUTRON_USE_NAMESPACES=n

Both installer.network.config.* and installer.config.* options will be merged into one config and used as the answer file for Packstack installer.installer

OpenStack director
^^^^^

Testers
-------
For list of supported testers invoke::

    $ ir-tester -h

Tempest
^^^^^^^

Rally
^^^^^
