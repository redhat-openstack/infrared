.. highlight:: plain

VIRSH
=====

Virsh provisioner is explicitly designed to be used for setup of virtual OpenStack environments.
Such environments are used to emulate production environment of `Tripleo installer`_
instances on one baremetal machine. It requires one prepared baremetal host (designated ``hypervisor``)
to be reachable through SSH initially.

First, Libvirt and KVM environment is installed and configured to provide virtualized environment.
Then, virtual machines are created for all requested nodes.
These VM's are used in `Tripleo installer`_ as undercloud, overcloud and auxiliary nodes.

Please see `Quickstart <quickstart.html>`_ guide where usage is demonstrated.

Network layout
""""""""""""""
Baremetal machine used as host for such setup is called `hypervisor`. The whole deployment is designed to
work within boundaries of this machine and (except public/natted traffic) shouldn't reach beyond.
The following layout is part of default setup defined in
`plugins defaults <https://github.com/rhosqeauto/InfraRed/blob/IR2/plugins/virsh/vars/topology/networks/3_nets.yml>`_::

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

.. User can also provide his own network layout (example `network-sample.yml <https://github.com/rhosqeauto/InfraRed/blob/master/settings/provisioner/virsh/topology/network/network.sample.yml>`_).

On `hypervisor`, there are 3 new bridges created with libvirt - data, management and external.
Most important is data network which does not have DHCP and NAT enabled.
This network can later be used as ``ctlplane`` for OSP director deployments (`Tripleo installer`_).
Other (usually physical) interfaces are not used (nic0, nic1, ...) except for public/natted traffic.
External network is used for SSH forwarding so client (or Ansible) can access dynamically created nodes.

`VIRSH` provisioner workflow:

 #. Setup libvirt and kvm environment

 #. Setup libvirt networks

 #. Download base image for undercloud (``--image-url``)

 #. Create desired amount of images and integrate to libvirt

 #. Define virtual machines with requested parameters (``--topology-nodes``)

 #. Start virtual machines

Environments prepared such in way are usually used as basic virtual infrastructure for `Tripleo installer`_.

.. note:: Virsh provisioner has currently idempotency issues, therefore ``infrared virsh ... --cleanup`` must be run before reprovisioning every time.


.. _`Tripleo installer`: missing.html
