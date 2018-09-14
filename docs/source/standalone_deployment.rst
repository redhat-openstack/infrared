Standalone deployment
=====================

Infrared allows to deploy tripleo openstack in stancalone mode. This means that
all the openstack services will be hosted on one node.
See https://blueprints.launchpad.net/tripleo/+spec/all-in-one for details.

To start deployment the ``standalone`` host should be added to the inventory.
For the virtual deployment, the ``virsh`` infrared plugin can be used for that::

    infrared virsh --topology-nodes standalone:1 \
                   --topology-network 1_net \
                   --host-address myvirthost.redhat.common
                   --host-key ~/.ssh/host-key.pem


After that start standalone deployment::

    ir tripleo-standalone --version 14
