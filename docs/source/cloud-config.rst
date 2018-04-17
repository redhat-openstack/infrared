Cloud Config
============

Collection of overcloud configuration tasks to run after Overcloud deploy (Overcloud post tasks)

Flags
-----

* ``--tasks``: Run one or more tasks to the cloud. separate with commas.

  .. code-block:: plain

      Example:
      infrared cloud-config --tasks create_external_network,compute_ssh,instance_ha
* ``--overcloud-stack``: The overcloud stack name.
* ``--resync``: Bool. Whether we need to resync services.

External Network
----------------
* ``--deployment-files``: Name of folder in cloud's user on undercloud, which containing the templates of the overcloud deployment.
* ``--network-protocol``: The overcloud network backend.
* ``--public-net-name``: Specifies the name of the public network.
.. note:: If not provided it will use the default one for the OSP version.
* ``--public-subnet``: Path to file containing different values for the subnet of the network above.
* ``--external-vlan``: An Optional external VLAN ID of the external network (Not the Public API network).

Scale Up/Down nodes
-------------------
* ``--scale-nodes``: List of compute nodes to be added.

  .. code-block:: plain

    Example:
    compute-3,compute-4,compute-5

* ``--node-name``: Name of the node to remove.

Ironic Configuration
--------------------
* ``vbmc-username``: VBMC username.
* ``vbmc-password``: VBMC password.
.. note:: Necessary when Ironic's driver is 'pxe_ipmitool' in OSP 11 and above.

Workload Launch
---------------
* ``--workload-image-url``: Image source URL that should be used for uploading the workload Glance image.
* ``--workload-memory``: Amount of memory allocated to test workload flavor.
* ``--workload-vcpu``: Amount of v-cpus allocated to test workload flavor.
* ``--workload-disk``: Disk size allocated to test workload flavor.
* ``--workload-index``: Number of workload objects to be created.
