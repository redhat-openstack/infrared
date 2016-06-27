.. highlight:: plain

Using InfraRed
================

General workflow
----------------

InfraRed framework is divided into three logically separated stages (tools):

* ``ir-provisioner``

* ``ir-installer``

* ``ir-tester``

You can get general usage information with the ``--help`` option::

  ir-<stage> --help

Output will display supported options you can pass to ``ir-<stage>``, as well as available positional arguments for current stage (e.g. for provisioner these are foreman, virsh, openstack, ...):

Also, you can invoke help for specific positional arguments (supported provisioners, in this case)::

  ir-<stage> virsh --help

.. note:: Positional arguments are generated dynamically from spec files - order and amount might change in time.


.. note:: Stages are physically separated, you can execute them in mixed (but meaningful) order. Example:

  .. code-block:: plain

    ir-provisioner virsh
    ir-installer ospd
    ir-tester tempest
    ir-installer ospd --scale
    ir-tester tempest

  Currently, executing different sub-commands of the same stage (i.e. ``ir-provisioner beaker`` and then ``ir-provisioner virsh``) is possible
  but the user must save the created inventory files (``hosts-provisioner``) between exectuions as they will overwrite each other

Passing parameters
^^^^^^^^^^^^^^^^^^

.. note:: By nature of the project, many configurable details like passwords, keys, certifcates, etc... cannot be stored in a public GitHub repo.
 We keep a private repo for internal Red Hat users that mirrors the ``settings tree``. Using the `Multi-settings <setup.html#private-settings>`_
 feature in ``infrared.cfg`` file, InfraRed will search those directories for files missing from the public settings directory.

InfraRed expects that selected workflow (playbook and roles) will be provided with all mandatory parameters. There are several ways to do it:

* Use `separate private configuration directory <setup.html#private-settings>`_

* Include standalone file(s) containing additional (private) settings as explicit input file(s) (``-i`` or ``--input`` parameters), for example:

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

* Use command line ``ir-<stage> --param1 --param2 ...``

.. note:: Best practice is store infrastructure-specific configuration file(s) in private repository and fetch such file(s) before deployment.

.. TODO(yfried) split to different files (either prov/inst/test or a single file for each sub-command)

Provisioners
------------
For list of supported provisioners invoke::

    $ ir-provisioner [<prov_name>] --help|-h

Beaker
^^^^^^
Entry point::

  playbooks/provisioner/beaker/main.yml

Beaker provisioner is designed to work with instances of `Beaker project <https://beaker-project.org>`_ at least version 22.3. It is based custom ansible module built on top of

.. code-block:: plain

  library/beaker_provisioner.py

script. While Beaker can support working with Kerberos, the usage is still limited, therefore authentication is done using XML-RPC API with credentials for dedicated user.

See appropriate value of ``ssh_pass`` for your ``beaker_username`` in `Website -> Account -> Preferences -> Root Password` if you didn't setup one. For proper XML-RPC calls ``cert_file`` must be provided.

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

.. warning::
   Currently, Foreman provisioning supports only cleanup of hosts::

     ir-provisioner [...] foreman [...] --cleanup

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

.. note:: You can also ommit the cloud parameter, then InfraRed expects you alredy sourced keystonerc of targeted cloud:

  .. code-block:: plain

    source keystonerc
    ir-provisioner openstack ...

Last important parameter is ``--dns`` which must be set to point to local DNS server in your infrastructure.

.. TODO - Someone elaborate here please what are the exact reasons and what exactly is affected.

Virsh
^^^^^
Entry point::

  playbooks/provisioner/virsh/main.yml

Virsh provisioner is explicitly designed to be used for setup of virtual OpenStack environments. Such environments are used to emulate production environment of `OpenStack director <execute.html#id1>`_ instances on one baremetal machine. It requires prepared baremetal host to be reachable through SSH initially. Topology created using virsh provisioner is called "virthost".

First, Libvirt and KVM environment is installed and configured to provide virtualized environment.  Then, virtual machines are created for all requested nodes. These VM's are used in `OSPd installer <execute.html#id2>`_ as undercloud, overcloud and auxiliary nodes.

Please see `Quickstart <quickstart.html>`_ guide where usage is demonstrated.

.. TODO - Network layout - chapter describing network in detail

Network layout
""""""""""""""
Baremetal machine used as host for such setup is called `virthost`. The whole deployment is designed to work within boundaries of this machine and (except public/natted traffic) shouldn't reach beyond. Following layout is part of default setup defined in `default.yml <https://github.com/rhosqeauto/InfraRed/blob/master/settings/provisioner/virsh/topology/network/default.yml>`_. User can also provide his own network layout (example `network-sample.yml <https://github.com/rhosqeauto/InfraRed/blob/master/settings/provisioner/virsh/topology/network/network.sample.yml>`_).

.. code-block:: plain

       Virthost
           |
           +--------+ nic0 - public IP
           |
           +--------+ nic1 - not managed
           |
             ...                                              Libvirt VM's
           |                                                        |
     ------+--------+ data bridge (ctlplane, 192.0.2/24)            +------+ data (nic0)
     |     |                                                        |
 libvirt --+--------+ management bridge (nat, dhcp, 172.16.0/24)    +------+ managementnt (nic1)
     |     |                                                        |
     ------+--------+ external bridge (nat, dhcp, 10.0.0/24)        +------+ external (nic2)

On virthost, there are 3 new bridges created with libvirt - data, management and external. Most important is data network which does not have dhcp and nat enabled. This network is used as ctlplane for OSP director deployments (`OSPd installer <execute.html#id2>`_). Other (usually physical) interfaces are not used (nic0, nic1, ...) except for public/natted traffic. External network is used for SSH forwarding so client (or ansible) can access dynamically created nodes.

Virsh provisioner workflow:

 #. Setup libvirt and kvm environment

 #. Setup libvirt networks

 #. Download base image for undercloud (``--image``)

 #. Create desired amount of images and integrate to libvirt

 #. Define virtual machines with requested parameters (``--topology-nodes``)

 #. Start virtual machines

Environments prepared such way are usually used as basic virtual infrastructure for `OSPd installer <execute.html#OpenStack-director>`_.

.. note:: Virsh provisioner has currently idempotency issues, therefore ``ir-provisioner virsh ... --cleanup`` must be run before reprovisioning every time.

Custom images
"""""""""""""
If you need to provide your own prepared images for virsh provisioner, you can use handy feature overriding “import_url” option::

    ir-provisioner ... \
    -e topology.nodes.<node name>.disks.disk1.import_url=http://.../image.qcow2 ... \
    ...

Installers
----------
For list of supported installers invoke::

    $ ir-installer [<installer_name>] --help|-h

Packstack
^^^^^^^^^
.. TODO: Revisit packstack as this was mostly copied from previous docs - I am really not sure here!
.. TODO: yfried: Add how packstack supports AIO topology
Entry point::

  playbooks/installer/packstack/main.yml

Infrared allows to use Packstack installer to install OpenStack::

    $ ir-installer --inventory hosts packstack --product-version=8

Required arguments are:

    * ``--product-version`` - the product version to install

Settings structure
""""""""""""""""""

The path for the main settings file for packstack installer::

  settings/installer/packstack/packstack.yml

This file provides defaults settings and default configuration options for various packstack answer files. Additional answer options can be added using the the following approaches:

* Using a non default config argument value::

    $ ... --config=basic_neutron.yml

* Using the extra-vars flags::

    $ ... --product-version=8 --extra-vars=installer.config.CONFIG_DEBUG_MODE=no

* Network based answer file options can be selected whether by choosing network backend or by modyfing config with --extra-vars::

    $ ... --product-version=8 --network=neutron.yml --netwrok-variant=neutron_gre.yml

    $ ... --product-version=8 --network=neutron.yml --netwrok-variant=neutron_gre.yml \
          --extra-vars=installer.network.config.CONFIG_NEUTRON_USE_NAMESPACES=n

Both `installer.network.config.*` and `installer.config.*` options will be merged into one config and used as the answer file for Packstack.

OpenStack director
^^^^^
Entry point::

  playbooks/installer/ospd/main.yml

There is one OSPd deployment type currently supported:

* Virthost (VH) setup - not really using baremetal nodes, they are emulated using virtual ones
* Baremetal (BM) setup - production use-case

nic1 - data
  * Referred to as "ctlplane" by `OSPd documentation <https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux_OpenStack_Platform/7/html/Director_Installation_and_Usage/>`_
  * Does not have dhcp and nat enabled (OSPd will later take dhcp/nat ownership for this network)
  * Used by OSPD to handle dhcp and pxe boot for overcloud nodes
  * Later used as primary interface for ssh by InraRed (Ansible)
  * Data between compute nodes and Ceph storage (if exists)
nic2 - management
  * Internal API for the overcloud services (services run REST queries against these interfaces (for example Neutron/Nova communication and neutron-server/neutron-agent communication))
  * Tenant network with tunnels (vxlan/gre/vlan) for internal data between OverCloud nodes. Examples:

    * VM (on compute-0) to VM (on compute-1)
    * VM (on compute-1) to Neutron Router (on Controller-3)
nic3 - external
  * public API for the overcloud services (OC users run REST queries against these interfaces)
  * The testers (i.e. Tempest) use this network to execute commands against the OverCloud API
  * Routes external traffic for nested VMs outside of the overcloud (connects to neutron external network and br-ex bridge...)
  * The testers (i.e. Tempest) use this network to ssh to the VMs (cirros) nested in the OverCloud

.. TODO: Add doc about BM setup, virthost is not enough!!!
.. TODO: Add OVB in future

OSPd is designed to be used in BM setup in production, however it is possible to use VH setup for automated testing, CI, e.g. when there is lack of BM hosts. BM setup deals with full scale deployment - contains deployment itself and infrastructure management. Virthost setup expects infrastructure prepared earlier during ir-provision stage. OSPd deployment in general consists of following steps:

* Undercloud deployment
* Virthost tweaks
* Image management
* Introspection
* Flavor setup
* Overcloud deployment

You can find full documentation at `Red Hat OpenStack director <https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux_OpenStack_Platform/7/html/Director_Installation_and_Usage/>`_.

Testers
-------
For list of supported testers invoke::

    $ ir-tester --help

.. TODO: Add doc about testers
.. Tempest
.. Rally
