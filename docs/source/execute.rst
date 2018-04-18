.. include:: warning.txt

.. highlight:: plain

Using InfraRed
==============

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

  playbooks/provisioner/foreman/main.yml

.. warning::
   Currently, Foreman provisioning supports only the ability to rebuild hosts (without the option change the operating system)::

     ir-provisioner [...] foreman [...]

Foreman provisioner is designed to work with instances of `Foreman project <https://theforeman.org>`_ at least version 1.6.3. It is based custom ansible module built on top of

.. code-block:: plain

  library/foreman_provisioner.py

Foreman provisioner expects that provisioned node has configured relevant puppet recipies to provide basic SSH access after provisioning is done.

To get more details on how to provision hosts using Foreman::

    $ ir-provisioner foreman --help

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

Cleanup
"""""""
`virsh` cleanup will discover virsh nodes and networks on the host and delete them as well as their matching disks.
To avoid cleanup of specific nodes/networks use extra vars ``ignore_virsh_nodes`` and ``ignore_virsh_nets``::

  ir-provisioner [...] virsh [...]  --cleanup \
      --host-address=example1.redhat.com \
      --host-key=~/.ssh/id_rsa \
      --extra-vars ignore_virsh_nodes=MY-NODE-0 \
      --extra-vars ignore_virsh_nets=MY-PERSISTENT-NETWORK

By default, cleanup will only ignore ``default`` network (automatically created by `libvirt`). Overriding the ``ignore_virsh_nets`` variable will delete this network unless explicitly specified

.. warning:: Arguments like ``images`` and ``topology`` are required by cleanup even though they are never used. This will be fixed in future versions.

.. warning:: Cleanup won't install libvirt packages and requirements. If `libvirtd` service is unavailable, cleanup be skipped

Network layout
""""""""""""""
Baremetal machine used as host for such setup is called `Virthost`_. The whole deployment is designed to work within boundaries of this machine and (except public/natted traffic) shouldn't reach beyond. Following layout is part of default setup defined in `default.yml <https://github.com/rhosqeauto/InfraRed/blob/master/settings/provisioner/virsh/topology/network/default.yml>`_. User can also provide his own network layout (example `network-sample.yml <https://github.com/rhosqeauto/InfraRed/blob/master/settings/provisioner/virsh/topology/network/network.sample.yml>`_).

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
^^^^^^^^^^^^^^^^^^
Entry point::

  playbooks/installer/ospd/main.yml

OSPd deployment in general consists of following steps:

* Undercloud deployment
* Virthost tweaks
* Image management
* Introspection
* Flavor setup
* Overcloud deployment

You can find full documentation at `Red Hat OpenStack director <https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux_OpenStack_Platform/>`_.

There are 2 OSPd deployment types currently supported.
The API is the same but different input is required and
different assumptions are made for each deployment type:

* Baremetal (BM)

  Normal deployment of openstack where all nodes are physical hosts.

  Users need to provide:
    * ``--deployment-files`` - directory with various files and templates, describing
      the OverCloud (such as ``instackenv.json``).
    * ``--undercloud-config`` - ``undercloud.conf`` file. If not provided,
      the `sample configuration file <http://docs.openstack.org/developer/tripleo-docs/installation/installing.html#installing-the-undercloud>`_
      will be used.
    * ``--instackenv-file`` - ``instackenv.json`` `file <http://docs.openstack.org/developer/tripleo-docs/environments/baremetal.html?highlight=instackenv#instackenv-json>`_.

  Both paths must be absolute paths::

        ir-installer ospd [...] --deployment-files=/absolute/path/to/templates/directory [...] --undercloud-config=/home/myuser/undercloud.conf

  The details of such directory can be found under `settings tree <https://github.com/rhosqeauto/InfraRed/tree/master/settings/installer/ospd/deployment/example>`_

.. TODO: replace link with actual details

* Virthost (VH)

  Using `virsh`_ provisioner, deploy openstack on virtual machines hosted on a single hypervisor (aka `Virthost`_).

  This is a common use-case for POC, development and testing, where hardware is limited.
  OSPD requires special customization to be nested on OpenStack clouds, so using local virsh VMs is a common solution.

  Expects the following network deployment (created by the ``virsh`` provisioner):

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

  To build a `Virthost`_ deployment, use the preset deployment-files provided in ``settings``::

    ir-installer ospd --deployment-files=$PWD/settings/installer/ospd/deployment/virt [...]

  InfraRed will generate ``undercloud.conf`` and ``instackenv.json`` configuration files if not provided explicitly.
  See `Quickstart <quickstart.html#ospd-quickstart>`_ guide for more details.
.. TODO: Add OVB in future


Hostnames
"""""""""

To simplify node management, InfraRed uses shorter names than the default names OSPD gives
the OverCloud nodes. For example, instead of ``overcloud-cephstorage-0`` the node will be called ``ceph-0``.
The full conversion details are `here <https://github.com/rhosqeauto/InfraRed/blob/master/roles/installer/ospd/overcloud/hostname/vars/main.yml>`_.

A user can provide customized `HostnameMap <http://docs.openstack.org/developer/tripleo-docs/advanced_deployment/node_placement.html?highlight=hostnameformat#custom-hostnames>`_
using ``--overcloud-hostname`` argument::

    ir-installer [...] ospd [...] --overcloud-hostname=special_hostnames.yml [...]

.. code-block:: yaml
   :caption: special_hostnames.yml

    HostnameMap:
        ceph-0: my_main_ceph_node
        ceph-1: another_storage_node
        controller-2: SPECIAL_MACHINE
        compute-0: BIG_HYPERVISOR

Note that the default naming template is the one described above
and not the one in the tripleo documentation (``overcloud-novacompute-0``).

.. note:: The naming convention and customization can be completely overridden if the ``--deployment-files``
    input contains a file called ``hostnames.yml`` following the tripleo `guidlines <http://docs.openstack.org/developer/tripleo-docs/advanced_deployment/node_placement.html>`_

Testers
-------
.. note:: Inventory file (``hosts``) should have ``tester`` group with 1 node in it.
    In ``ospd`` this is usually the undercloud. In ``packstack`` this is usually a dedicated node.

For list of supported testers invoke::

    $ ir-tester --help

.. TODO: Add doc about testers
.. Rally

Tempest
^^^^^^^

.. note:: `InfraRed` uses a python script to configure `Tempest`. Currently that script is only available in
 `Red Hat's Tempest fork <https://github.com/redhat-openstack/tempest>`_, so `InfraRed` will clone that repo
 as well in order to use that script.

Use ``--tests`` to provide a list of test sets to execute. Each test set is defined in
`settings tree <https://github.com/rhosqeauto/InfraRed/tree/master/settings/tester/tempest/tests>`_
And will be executed separately.

To import Tempest Plugins from external repos, ``tests`` files should contain ``plugins`` dict.
`InfraRed` will clone those plugins from source and install them. Tempest will be able to discover
and execute tests from those repos as well.

.. code-block:: yaml
   :emphasize-lines: 6-8
   :caption: settings/tester/tempest/tests/neutron.yml

   ---
   name: neutron
   test_regex: "^neutron.tests.tempest"
   whitelist: []
   blacklist: []
   plugins:
     neutron:
       repo: "https://github.com/openstack/neutron.git"


Scripts
-------
Archive
^^^^^^^
This script will create a portable package which can be used to access an environment deployed by InfraRed from any
machine. The archive script archives the relevant SSH & inventory files using tar. One can later use those files
from anywhere in order to SSH and run playbook against the inventory hosts.

To get the full details on how to use the archive script invoke::

    $ ir-archive --help

Basic usage of archive script::

    $ ir-archive

.. note:: Unless supplying paths to all relevant files, please run this script from the InfraRed project dir

This creates a new tar file (IR-Archive-[date/suffix].tar) containing the files mentioned above while de-referencing local absolute paths of the SSH keys so they can be accessed from anywhere.

Usage examples:

* Untar the archive file::

    tar -xvf IR-Archive-2016-07-11_10-31-28.tar

.. note:: Make sure to extract the files into the InfraRed project dir


* Use the SSH config file to access your provisioned nodes::

    ssh -F ansible.ssh.config.2016-07-11_10-31-28 controller-0

* Execute ansible Ad-Hoc command / Run playbook against the nodes in the archived inventory file::

    ansible -i hosts-2016-07-11_10-31-28 all -m setup

* Use the archived files with InfraRed::

    mv ansible.ssh.config.2016-07-11_10-31-28 ansible.ssh.config
    ir-installer --inventory hosts-2016-07-11_10-31-28 ospd ...

.. _Virthost: setup.html#virthost-machine
