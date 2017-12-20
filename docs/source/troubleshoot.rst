============
Troubleshoot
============

This page will list common pitfalls or known issues, and how to overcome them

Ansible Failures
================

Unreachable
~~~~~~~~~~~

Symptoms:
`````````

.. code-block:: text

    fatal: [hypervisor]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh.", "unreachable": true}

Solution:
`````````

When Ansible fails because of ``UNREACHABLE`` reason, try to validate SSH
credentials and make sure that all host are SSH-able.

In the case of ``virsh`` plugin, it's clear from the message above that the designated hypervisor is unreachable. Check that:

#. ``--host-address`` is a reachable address (IP or FQDN).
#. ``--host-key`` is a **private** (not **public**) key file and that its permissions are correct.
#. ``--host-user`` (defaults to ``root``) exits on the host.
#. Try to manually ssh to the host using the given user private key::

    ssh -i $HOST_KEY $HOST_USER@$HOST_ADDRESS


Virsh Failures
==============

Cannot create VM's
~~~~~~~~~~~~~~~~~~

Symptoms:
`````````
Virsh cannot create a VM and displays the following message::

    ERROR    Unable to add bridge management port XXX: Device or resource busy
    Domain installation does not appear to have been successful.
    Otherwise, you can restart your domain by running:
      virsh --connect qemu:///system start compute-0
    otherwise, please restart your installation.

Solution:
`````````
This often can be caused by the misconfiguration of the hypervisor.
Check that all the ``ovs`` bridges are properly configured on the hypervisor::

    $ ovs-vsctl show

    6765bb7e-8f22-4dbe-848f-eaff2e94ed96
    Bridge brbm
        Port "vnet1"
            Interface "vnet1"
                error: "could not open network device vnet1 (No such device)"
        Port brbm
            Interface brbm
                type: internal
    ovs_version: "2.6.1"


To fix the problem remove the broken bridge::

    $ ovs-vsctl del-br brbm


Cannot activate IPv6 Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Symptoms:
`````````
Virsh fails on task 'check if network is active' or on task 'Check if IPv6 enabled on host' with one of the following error messages::

    Failed to add IP address 2620:52:0:13b8::fe/64 to external

    Network 'external' requires IPv6, but modules aren't loaded...

Solution:
`````````
Ipv6 is disabled on hypervisor. Please make sure to enable IPv6 on the hypervisor before creating network with IPv6,
otherwise, IPv6 networks will be created but will remain in 'inactive' state.

One possible solution on RH based OSes, is to enable IPv6 in kernel cmdline::

    # sed -i s/ipv6.disable=1/ipv6.disable=0/ /etc/default/grub
    # grub2-mkconfig -o /boot/grub2/grub.cfg
    # reboot


Frequently Asked Questions
==========================

Where's my inventory file?
~~~~~~~~~~~~~~~~~~~~~~~~~~

I'd like to run some personal Ansible playbook and/or "ad-hoc" but I can't find my inventory file

All Ansible environment files are read from, and written to, `workspaces <workspace>`_
Use ``infrared workspace inventory`` to fetch a symlink to the active workspace's inventory
or ``infrared workspace inventory WORKSPACE`` for any workspace by name::

    ansible -i `infrared workspace inventory` all -m ping

    compute-0 | SUCCESS => {
        "changed": false,
        "ping": "pong"
    }
    compute-1 | SUCCESS => {
        "changed": false,
        "ping": "pong"
    }
    controller-0 | SUCCESS => {
        "changed": false,
        "ping": "pong"
    }
    localhost | SUCCESS => {
        "changed": false,
        "ping": "pong"
    }
    hypervisor | SUCCESS => {
        "changed": false,
        "ping": "pong"
    }
    undercloud-0 | SUCCESS => {
        "changed": false,
        "ping": "pong"

