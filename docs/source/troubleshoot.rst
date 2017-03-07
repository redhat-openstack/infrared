Troubleshoot
============

This page will list common pitfalls or known issues, and how to overcome them

Ansible Failures
----------------

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

