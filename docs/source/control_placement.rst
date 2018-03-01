Controlling Node Placement
--------------------------

Overview
========

The default behavior for the director is to randomly select nodes for each role, usually based on their profile tag.
However, the director provides the ability to define specific node placement. This is a useful method to:

    * Assign specific node IDs
    * Assign custom hostnames
    * Assign specific IP addresses

InfraRed support this method in `tripleo-overcloud <tripleo-overcloud.html#controlling-node-placement>`_ plugin.

Defining topology and controlling node placement
================================================

The examples show how to provision several nodes with `virsh <virsh.html>`_ plugin and then how to use controlling
node placement option during Overcloud Deploy.

Topology
^^^^^^^^
Topology include 1 undercloud, 3 controllers, 2 compute and 3 ceph nodes::

    $ ir virsh -vvvv
        --topology-nodes=undercloud:1,controller:3,compute:2,ceph:3 \
        --host-address=seal52.qa.lab.tlv.redhat.com \
        --host-key ~/.ssh/my-prov-key \
        [...]

Overcloud Install
^^^^^^^^^^^^^^^^^
This step require `Undercloud <tripleo-undercloud.html>`_ to be installed and tripleo-overcloud introspection and tagging to be done::

    $ ir tripleo-overcloud -vvvv
        --version=12 \
        --deploy=yes \
        --deployment-files=virt \
        --specific-node-ids yes \
        --custom-hostnames ceph-0=storage-0,ceph-1=storage-1,ceph-2=storage-2,compute-0=novacompute-0,compute-1=novacompute-1,controller-0=ctrl-0,controller-1=ctrl-1,controller-2=ctrl-2 \
        --predictable-ips yes \
        --overcloud-templates ips \
        [...]

.. warning:: Currently node IPs need to be provided as user template with --overcloud-templates

InfraRed Inventory
^^^^^^^^^^^^^^^^^^
After Overcloud install, InfraRed directory contains the overcloud nodes with their new hostnames::

    $ ir workspace node-list
    +---------------+------------------------------+-------------------------------------------------------+
    | Name          | Address                      | Groups                                                |
    +---------------+------------------------------+-------------------------------------------------------+
    | undercloud-0  | 172.16.0.5                   | tester, undercloud, openstack_nodes                   |
    +---------------+------------------------------+-------------------------------------------------------+
    | hypervisor    | seal52.qa.lab.tlv.redhat.com | hypervisor, shade                                     |
    +---------------+------------------------------+-------------------------------------------------------+
    | novacompute-0 | 192.168.24.9                 | overcloud_nodes, compute, openstack_nodes             |
    +---------------+------------------------------+-------------------------------------------------------+
    | novacompute-1 | 192.168.24.21                | overcloud_nodes, compute, openstack_nodes             |
    +---------------+------------------------------+-------------------------------------------------------+
    | storage-2     | 192.168.24.16                | overcloud_nodes, ceph, openstack_nodes                |
    +---------------+------------------------------+-------------------------------------------------------+
    | storage-1     | 192.168.24.6                 | overcloud_nodes, ceph, openstack_nodes                |
    +---------------+------------------------------+-------------------------------------------------------+
    | storage-0     | 192.168.24.18                | overcloud_nodes, ceph, openstack_nodes                |
    +---------------+------------------------------+-------------------------------------------------------+
    | ctrl-2        | 192.168.24.10                | overcloud_nodes, network, controller, openstack_nodes |
    +---------------+------------------------------+-------------------------------------------------------+
    | ctrl-0        | 192.168.24.15                | overcloud_nodes, network, controller, openstack_nodes |
    +---------------+------------------------------+-------------------------------------------------------+
    | ctrl-1        | 192.168.24.14                | overcloud_nodes, network, controller, openstack_nodes |
    +---------------+------------------------------+-------------------------------------------------------+

