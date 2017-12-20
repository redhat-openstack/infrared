OpenStack
=========

Provision VMs on an exiting OpenStack cloud, using native ansible's `cloud modules <http://docs.ansible.com/ansible/list_of_cloud_modules.html#openstack>`_.

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

    ``clouds.yml`` is expected in either ``~/.config/openstack`` or ``/etc/openstack`` directories
    according to `documentation <http://docs.openstack.org/developer/os-client-config/#config-files>`_:

        .. note:: You can also omit the cloud parameter, and `infrared` will sourced openstackrc file:

          .. code-block:: plain

                source keystonerc
                infrared openstack openstack ...

* ``--key-file``: Private key that will be used to ssh to the provisioned VMs.
    Chosen matching public key will be uploaded to the OpenStack account,
    unless ``--key-name`` is provided
* ``--key-name``: Name of an existing `keypair` under the OpenStack account.
    `keypair` should hold the public key that matches the provided private ``--key-file``.
    Use ``openstack --os-cloud cloud_name keypair list`` to list available keypairs.
* ``--dns``: A Local DNS server used for the provisioned networks and VMs.
    If not provided, OpenStack will use default DNS settings, which, in most cases,
    will not resolve internal URLs.

Topology
--------

* ``--prefix``: prefix all resources with a string.
    Use this with shared tenants to have unique resource names.

    .. note:: ``--prefix "XYZ"`` will create router named ``XYZrouter``.
        Use ``--prefix "XYZ-"`` to create ``XYZ-router``

* ``--topology-network``: Description of the network topology.
    By default, 3 networks will be provisioned with 1 router.
    2 of them will be connected via the router to an external network discovered automatically
    (when more than 1 external network is found, the first will be chosen)::

If we look in the ``3_nets.yml`` file, we will see this::

    networks:
            net1:
                <snip>
            net2:
                name: "management"                 # the network name
                external_connectivity: yes         # whether we want it externally accessible
                ip_address: "172.16.0.1"           # the IP address of the bridge
                netmask: "255.255.255.0"
                forward:                           # forward method
                    type: "nat"
                dhcp:                              # omit this if you don't want a DHCP
                    range:                         # the DHCP range to provide on that network
                        start: "172.16.0.2"
                        end: "172.16.0.100"
                    subnet_cidr: "172.16.0.0/24"
                    subnet_gateway: "172.16.0.1"
                floating_ip:                       # whether you want to "save" a range for assigning IPs
                    start: "172.16.0.101"
                    end: "172.16.0.150"
            net3:
                <snip>

* ``--topology-nodes``: `KeyValueList` description of the nodes.
    A floating IP will be provisioned on a designated network.

For more information about the structure of the topology files and how to create your own,
please refer to `Topology`_ and `Virsh plugin`_ description.

* ``--image``: default image name or id for the VMs
    use ``openstack --os-cloud cloud_name image list`` to see a list of available images

* ``--cleanup`` Boolean. Whether to provision resources, or clean them from the tenant.
    `Infrared` registers all provisioned resources to the `workspace <workspace.html>`_ on creation,
    and will clean only registered resources::

        infrared openstack --cleanup yes

.. _`Topology`: topology.html
.. _`Virsh plugin`: virsh.html#topology
.. _`os-client-config`: http://docs.openstack.org/developer/os-client-config
