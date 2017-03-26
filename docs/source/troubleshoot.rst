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
    If it was, you can restart your domain by running:
      virsh --connect qemu:///system start compute-0
    otherwise, please restart your installation.

Solution:
`````````
This often can be caused by the misconfiguration of the hypervisor.
Check that all the ovs bridges are properly configured on the hypervisor::

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
