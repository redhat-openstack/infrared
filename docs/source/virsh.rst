.. highlight:: text

Virsh
=====
Virsh provisioner is explicitly designed to be used for setup of virtual environments.
Such environments are used to emulate production environment like `tripleo-undercloud`_
instances on one baremetal machine. It requires one prepared baremetal host (designated ``hypervisor``)
to be reachable through SSH initially.

.. toctree::
   :maxdepth: 1
   :caption: Requirements

   hypervisor

First, Libvirt and KVM are installed and configured to provide a virtualized environment.
Then, virtual machines are created for all requested nodes.

Topology
--------
The first thing you need to decide before you deploy your environment is the ``Topology``.
This refers to the number and type of VMs in your desired deployment environment.
If we use OpenStack as an example, a topology may look something like:

    * 1 VM called undercloud
    * 1 VM called controller
    * 1 VM called compute

To control how each VM is created, we have creates a YAML file that describes the
specification of each VM.
For more information about the structure of the topology files and how to create your own,
please refer to `Topology <topology.html>`_.

Please see `Bootstrap <bootstrap.html>`_ guide where usage is demonstrated.

* ``--host-memory-overcommit``
    By default memory overcommitment is false and provision will fail if Hypervisor's free
    memory is lower than required memory for all nodes. Use `--host-memory-overcommit True`
    to change default behaviour.

Network layout
~~~~~~~~~~~~~~
Baremetal machine used as host for such setup is called `hypervisor`. The whole deployment is designed to
work within boundaries of this machine and (except public/natted traffic) shouldn't reach beyond.
The following layout is part of default setup defined in
`plugins defaults <https://github.com/redhat-openstack/infrared/blob/master/plugins/virsh/defaults/topology/network/3_nets.yml>`_::

              hypervisor
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

On `hypervisor`, there are 3 new bridges created with libvirt - data, management and external.
Most important is data network which does not have DHCP and NAT enabled.
This network can later be used as ``ctlplane`` for OSP director deployments (`tripleo-undercloud`_).
Other (usually physical) interfaces are not used (nic0, nic1, ...) except for public/natted traffic.
External network is used for SSH forwarding so client (or Ansible) can access dynamically created nodes.

NAT Forwarding
^^^^^^^^^^^^^^

By default, all networks above are `NATed`_, meaning that they
private networks only reachable via the `hypervisor` node.
`infrared` configures the nodes SSH connection to use the `hypervisor` host as
proxy.

Bridged Network
^^^^^^^^^^^^^^^

Some use-cases call for `direct access`_ to some of the nodes.
This is achieved by adding a network with ``forward: bridge`` in its attributes to the
network-topology file, and marking this network as external network on the relevant node
files.

The result will create a virtual bridge on the `hypervisor` connected to the main NIC by default.
VMs attached to this bridge will be served by the same LAN as the `hypervisor`.

To specify any secondary NIC for the bridge, the ``nic`` property should be added to the network
file under the bridge network::

    net4:
        name: br1
        forward: bridge
        nic: eth1


.. warning:: Be careful when using this feature. For example, an ``undercloud`` connected
    in this manner can disrupt the LAN by serving as an unauthorized DHCP server.

Fore example, see ``tripleo`` `node <tripleo>`_ used in conjunction with ``3_net_1_bridge``
`network file <1_bridge>`_::

   infrared virsh [...] --topology-nodes ironic:1,[...] --topology-network 3_net_1_bridge [...]

.. _`direct access`: https://wiki.libvirt.org/page/Networking#Bridged_networking_.28aka_.22shared_physical_device.22.29
.. _`NATed`: https://wiki.libvirt.org/page/Networking#NAT_forwarding_.28aka_.22virtual_networks.22.29
.. _`ironic`: https://github.com/redhat-openstack/infrared/blob/stable/plugins/virsh/defaults/topology/nodes/tripleo.yml
.. _`1_bridge`: https://github.com/redhat-openstack/infrared/blob/stable/plugins/virsh/defaults/topology/network/3_nets_1_bridge.yml


Workflow
--------

 #. Setup libvirt and kvm environment

 #. Setup libvirt networks

 #. Download base image for undercloud (``--image-url``)

 #. Create desired amount of images and integrate to libvirt

 #. Define virtual machines with requested parameters (``--topology-nodes``)

 #. Start virtual machines

Environments prepared such in way are usually used as basic virtual infrastructure for `tripleo-undercloud`_.

.. note:: Virsh provisioner has idempotency issues, so ``infrared virsh ... --kill`` must be run before reprovisioning every time
          to remove libvirt resources related to active hosts form workspace inventory or ``infrared virsh ... --cleanup`` to remove ALL domains
          and nettworks (except  'default') from hypervisor.




.. _`tripleo-undercloud`: tripleo-undercloud.html
.. _`tripleo-overcloud`: tripleo-overcloud.html


Topology Extend
---------------

* ``--topology-extend``: Extend existing deployment with nodes provided by topology.
  If ``--topology-extend`` is True, all nodes from ``--topology-nodes`` will be
  added as new additional nodes

  .. code-block:: shell

     infrared virsh [...] --topology-nodes compute:1,[...] --topology-extend yes [...]


Topology Shrink
---------------

* ``--remove-nodes``: Provide option for removing of nodes from existing topology::

    infrared virsh [...] --remove-nodes compute-2,compute3

.. warning:: If try to extend topology after you remove node with index lower than maximum, extending will fail.
             For example, if you have 4 compute nodes (compute-0,compute-1,compute-2,compute-3), removal of any
             node different than compute-3, will cause fail of future topology extending.
