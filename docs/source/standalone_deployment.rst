Standalone deployment
=====================

Infrared allows to deploy tripleo openstack in stancalone mode. This means that
all the openstack services will be hosted on one node.
See https://blueprints.launchpad.net/tripleo/+spec/all-in-one for details.

To start deployment the ``standalone`` host should be added to the inventory.
For the virtual deployment, the ``virsh`` infrared plugin can be used for that::

    infrared virsh --topology-nodes standalone:1 \
                   --topology-network 1_net \
                   --image-url <rhel8.qcow> \
                   --host-address myvirthost.redhat.common
                   --host-key ~/.ssh/host-key.pem

Note you should insert the correct URL to a RHEL8 image above.

After that start standalone deployment::

    infrared tripleo-standalone --version 15
