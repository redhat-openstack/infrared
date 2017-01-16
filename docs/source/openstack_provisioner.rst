OpenStack
=========

Provision VMs from an exiting OpenStack cloud, using native ansible's `cloud modules <http://docs.ansible.com/ansible/list_of_cloud_modules.html#openstack>`_.

OpenStack Cloud Details
-----------------------
* ``--cloud``: reference to OpenStack cloud credentials, using `os-client-config`_
    This library expects properly configured ``cloud.yml`` file:

        .. code-block:: plain
           :caption: clouds.yml

           clouds:
               cloud_name:
                   auth_url: http://openstack_instance:5000/v2.0
                   username: <username>
                   password: <password>
                   project_name: <project_name>

        ``cloud_name`` can be then referenced with ``--cloud`` option::

            infrared openstack --cloud cloud_name ...

        .. note:: You can also omit the cloud parameter, and InfraRed will sourced openstackrc file:

          .. code-block:: plain

                source keystonerc
                infrared openstack openstack ...

* ``--key-file``: Private key that will be used to ssh to the provisioned VMs.
    Its public key will be uploaded to the OpenStack account, unless ``--key-name`` is provided
* ``--key-name``: Name of an existing `keypair` under the OpenStack account, that matches the provided ``--key-file``.
    Use ``openstack --os-cloud cloud_name keypair list`` to see a list of available keypairs.
* ``--dns``: A Local DNS server used for the provisioned networks and VMs

.. TODO - Someone elaborate here please what are the exact reasons for not using default DNS and what exactly is affected.


Topology
--------
* ``--prefix``: prefix all resources with a string.
    Use this with shared tenants to have unique resource names.

    .. note:: ``--prefix "XYZ"`` will create router named ``XYZrouter``.
        Use ``--prefix "XYZ-"`` to create ``XYZ-router``

* ``--topology-network``: Description of the network topology.
    By default, 3 networks will be provisioned with 1 router.
    2 of them will be connected via the router to an external network discovered automatically
    (when more than 1 external network is found, the first will be chosen).

* ``--topology-nodes``: `KeyValueList` description of the nodes.
    A floating IP will be provisioned on a designated network.

.. todo(yfried): create description of topology input in a different doc

* ``--image``: default image name or id for the VMs
    use ``openstack --os-cloud cloud_name image list`` to see a list of available images

.. _`os-client-config`: http://docs.openstack.org/developer/os-client-config

* ``--cleanup`` Boolean. Whether to provision resources, or clean them from the tenant.
    `InfraRed` registers all provisioned resources to the `profile <profile.html>`_ on creation,
    and will clean only registered resources::

        infrared openstack --cleanup yes
