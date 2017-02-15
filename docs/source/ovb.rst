OVB deployment
==============

OVB (openstack virtual baremetal) allows to user openstack instances
to be used as the baremetal nodes during the tripleo deployments.

The InfraRed OVB implementation is based the
`openstack-virtual-baremetal <http://openstack-virtual-baremetal.readthedocs.io/en/latest/introduction.html>`_ project.

We strongly recommended to read documentation for that project prior moving next in that document.

OVB architecture overview
-------------------------

An OVB setup requires additional node to be present: Baremetal Controller (BMC).
This nodes captures all the IPMI requests dedicated to the OVB nodes and handles the
machine power on/off operations, boot device change and other operations performed
during the introspection phase.

Network architecture overview::

         +--------------+   Data   +--------+
         |              |  network |        |
         |  Undercloud  +----+---->+  OVB1  |
         |              |    |     |        |
         +-------+------+    |     +--------+
                 |           |
    Management   |           |     +--------+
       network   |           |     |        |
         +-------+------+    +---->|  OVB2  |
         |              |    |     |        |
         |      BMC     |    |     +--------+
         |              |    |
         +--------------+    |     +--------+
                             |     |        |
                             +---->+  OVB3  |
                                   |        |
                                   +--------+

The BMC node should be connected to the management network. InfraRed brings up an IP address on own management interface
for every OVB node. This allows InfraRed to handle IPMI commands coming from the undercloud.
Those IP are also used to generate the ``instackenv.json`` file.

For example, during the introspection phase, when the BMC sees the power off request for the
OVB1 node, it perfroms a sutdown for the instance which corresponds to the OVB1 on the host cloud.

Provision ovb nodes
-------------------

In order to provision ovb nodes, the `openstack provisioner <openstack_provisioner.html>`_ can be used::

    ir openstack -vvvv -o provision.yml \
        --cloud=qeos7 \
        --prefix=example-ovb- \
        --topology-nodes=ovb_undercloud:1,bmc:1,ovb_controller:1,ovb_compute:1 \
        --topology-network=3_nets_ovb  \
        --key-file ~/.ssh/example-key.pem \
        --key-name=example-jenkins \
        --image=rhel-guest-image-7.3-35_3nics


The ``--topology-nodes``  options should include the ``bmc`` instance. Also instead of
standard compute and controller nodes the appropriate nodes with the ``ovb`` prefix should be used.
Such ovb node settings file holds several additional properties:
  * instance ``image`` details. Currently the ``ipxe-boot`` image should be used for all the ovb nodes. Only that image allows to boot from the network after restart.
  * ovb group in the groups section
  * network topology (nic's order)

For example, the ovb_compute settings can hold the following properties::

    node_dict:
        name: compute
        image:
            name: "ipxe-boot"
            ssh_user: "root"
        interfaces:
            nic1:
                network: "data"
            nic2:
                network: "management"
            nic3:
                network: "external"
        external_network: external

        groups:
            - compute
            - openstack_nodes
            - overcloud_nodes
            - ovb


The ``--topology-network`` should specify the topology with at 3 networks: data, management and external:
  - data network is used by the Tripleo to provision the overcloud nodes
  - management is used by the BMC to control IPMI operations
  - external holds floating ip's and used by InfraRed to access the nodes
DHCP should be enabled only for the external network.
Infrared provides the default ``3_nets_ovb`` network topology that allows to deploy the OVB setup.

The ``--image`` option should point to the image with the 3 nics configured for every
network. The nic's order should correspond to the network topology described in the ovb node settings files.


Install openstack with Tripleo
------------------------------

To install openstack on ovb nodes the process is almost standard with small deviation.

The undercloud can be installed by running::

    infrared tripleo-undercloud -v \
        --version 10 \
        --images-task rpm

The overcloud installation can be run with::

    infrared tripleo-overcloud -v \
        --version 10 \
        --deployment-files ovb \
        --public-network=yes \
        --public-subnet=ovb_subnet \
        --network-protocol ipv4 \
        --post=yes \
        --introspect=yes \
        --tagging=yes

Here some ovb specific option should be considered:
  - if host cloud is not patched and not configured for the OVB deployments the ``--deployment-files`` should point to the ovb templates to skip unsupported features. See the `OVB limitations`_ for details
  - the ``--public_subnet`` should point to the subnet settings to match with the OVB network topology and allocation addresses

As the result the fully functional overcloud will be deployed into the OVB nodes.

OVB limitations
---------------

The OVB approach requires a host cloud to be `patched and configured <http://openstack-virtual-baremetal.readthedocs.io/en/latest/host-cloud/setup.html>`_.
Otherwise the following features will **NOT** be available:
   - Network isolation
   - HA (high availability). Setup with more that 1 control, 1 compute, etc is not allowed.
   - Boot from network. This can be workaround by using the `ipxe_boot <https://github.com/cybertron/openstack-virtual-baremetal/tree/master/ipxe/elements/ipxe-boot-image>`_ image for the OVB nodes.


