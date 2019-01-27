TripleO Overcloud
=================

Deploys a TripleO overcloud from an existing undercloud

Stages Control
--------------

Run is broken into the following stages. Omitting any of the flags (or setting it to ``no``) will skip that stage

* ``--introspect`` the overcloud nodes
* ``--tag`` overcloud nodes with proper flavors
* ``--deploy`` overcloud of given ``--version`` (see below)

Containers
----------

* ``--containers``: boolean. Specifies if containers should be used for deployment. Default value: True

.. note:: Containers are supported by OSP version >=12.

* ``--container-images-packages``: the pairs for container images and packages URL(s) to install into those images.
    Container images don't have any yum repositories enabled by default, hence specifying URL of an RPM to
    install is mandatory. This option can be used multiple times for different container images.

.. note:: Only specified image(s) will get the packages installed. All images that depend on an updated image
      have to be updated as well (using this option or otherwise).

Example::

    --container-images-packages openstack-opendaylight-docker=https://kojipkgs.fedoraproject.org//packages/tmux/2.5/3.fc27/x86_64/tmux-2.5-3.fc27.x86_64.rpm,https://kojipkgs.fedoraproject.org//packages/vim/8.0.844/2.fc27/x86_64/vim-minimal-8.0.844-2.fc27.x86_64.rpm

* ``--container-images-patch``: comma, separated list of docker container images to patch using '/patched_rpm' yum repository.
    Patching involves 'yum update' inside the container. This feature is not supported when ``registry-undercloud-skip``
    is set to True. Also, if this option is not specified, InfraRed auto discovers images that should be updated. This option
    may be used to patch only a specific container image(s) without updating others that could be normally patched.

Example::

    --container-images-patch openstack-opendaylight,openstack-nova-compute

* ``--registry-undercloud-skip``: avoid using and mass populating the undercloud registry.
    The registry or the ``registry-mirror`` will be used directly when possible, recommended using this option
    when you have a very good bandwidth to your registry.
* ``--registry-mirror``: the alternative docker registry to use for deployment.
* ``--registry-namespace``: the alternative docker registry namespace to use for deployment.

* The following options define the ceph container:
    ``--registry-ceph-tag``: tag used with the ceph container. Default value: latest
    ``--registry-ceph-namespace``: namesapce for the ceph container

Deployment Description
----------------------

* ``--deployment-files``: Mandatory.
    Path to a directory, containing heat-templates describing the overcloud deployment.
    Choose ``virt`` to enable preset templates for virtual POC environment (`virsh`_ or `ovb`_).
* ``--instackenv-file``:
    Path to the instackenv.json configuration file used for introspection.
    For `virsh`_ and `ovb`_ deployment, `infrared` can generate this file automatically.
* ``--version``: TripleO release to install.
    Accepts either an integer for RHEL-OSP release, or a community release
    name (``Liberty``, ``Mitaka``, ``Newton``, etc...) for RDO release
* The following options define the number of nodes in the overcloud:
    ``--controller-nodes``, ``--compute-nodes``, ``--storage-nodes``.
    If not provided, will try to evaluate the exiting nodes and default to ``1``
    for ``compute``/``controller`` or ``0`` for ``storage``.
* ``--hybrid``: Specifies whether deploying a hybrid environment.
    When this flag it set, the user should pass to the ``--instackenv-file`` parameter a link to a JSON/YAML file.
    The file contains information about the bare-metals servers that will be added to the instackenv.json file during introspection.
* ``--environment-plan``/``-p``: Import environment plan YAML file that details the plan to be deployed by TripleO.
    Beside specifying Heat environments and parameters, one can also provide parameters for TripleO Mistral workflows.

    .. warning:: This option is supported by RHOSP version 12 and greater.

    Below are examples of a JSON & YAML files in a valid format:

    .. code-block:: yaml
       :caption: bm_nodes.yml

       ---
       nodes:
         - "name": "aaa-compute-0"
           "pm_addr": "172.16.0.1"
           "mac": ["00:11:22:33:44:55"]
           "cpu": "8"
           "memory": "32768"
           "disk": "40"
           "arch": "x86_64"
           "pm_type": "pxe_ipmitool"
           "pm_user": "pm_user"
           "pm_password": "pm_password"
           "pm_port": "6230"

         - "name": "aaa-compute-1"
           "pm_addr": "172.16.0.1"
           "mac": ["00:11:22:33:44:56"]
           "cpu": "8"
           "memory": "32768"
           "disk": "40"
           "arch": "x86_64"
           "pm_type": "pxe_ipmitool"
           "pm_user": "pm_user"
           "pm_password": "pm_password"
           "pm_port": "6231"

    .. code-block:: json
       :caption: bm_nodes.json

       {
         "nodes": [
           {
            "name": "aaa-compute-0",
            "pm_addr": "172.16.0.1",
            "mac": ["00:11:22:33:44:55"],
            "cpu": "8",
            "memory": "32768",
            "disk": "40",
            "arch": "x86_64",
            "pm_type": "pxe_ipmitool",
            "pm_user": "pm_user",
            "pm_password": "pm_password",
            "pm_port": "6230"
           },
           {
            "name": "aaa-compute-1",
            "pm_addr": "172.16.0.1",
            "mac": ["00:11:22:33:44:56"],
            "cpu": "8",
            "memory": "32768",
            "disk": "40",
            "arch": "x86_64",
            "pm_type": "pxe_ipmitool",
            "pm_user": "pm_user",
            "pm_password": "pm_password",
            "pm_port": "6231"
           }
         ]
       }


Overcloud Options
-----------------
* ``--overcloud-ssl``: Boolean. Enable SSL for the overcloud services.

* ``--overcloud-debug``: Boolean. Enable debug mode for the overcloud services.

* ``--overcloud-templates``: Add extra environment template files or custom templates
    to "overcloud deploy" command. Format:

    .. code-block:: yaml
       :caption: sahara.yml

       ---
       tripleo_heat_templates:
           - /usr/share/openstack-tripleo-heat-templates/environments/services/sahara.yaml

    .. code-block:: yaml
       :caption: ovs-security-groups.yml

       ---
       tripleo_heat_templates:
           []

       custom_templates:
           parameter_defaults:
               NeutronOVSFirewallDriver: openvswitch

* ``--overcloud-script``: Customize the script that will deploy the overcloud.
    A path to a ``*.sh`` file containing ``openstack overcloud deploy`` command.
    This is for advance users.

* ``--heat-templates-basedir``: Allows to override the templates base dir
    to be used for deployment. Default value: "/usr/share/openstack-tripleo-heat-templates"

* ``--resource-class-enabled``: Allows to enable or disable scheduling based on resource classes.
    Scheduling based on resource classes, a Compute service flavor is able to use the
    node's resource_class field (available starting with Bare Metal API version 1.21)
    for scheduling, instead of the CPU, RAM, and disk properties defined in the flavor.
    A flavor can request exactly one instance of a bare metal resource class.
    For more information about this feature, visit `Openstack documentation <https://docs.openstack.org/ironic/latest/install/configure-nova-flavors.html#scheduling-based-on-resource-classes>`_.

    To disable scheduling based on resource classes:

    .. code-block:: shell

       --resource-class-enabled False

.. note::
    * Scheduling based on resource classes is supported by OSP version >=12.
    * Scheduling based on resource classes is enabled by default for OSP version >=12.

* ``--resource-class-override``: Allows to create custom resource class and associate it with flavor and instances.
    The `node` field supports `controller` or `controller-0` patterns or list
    of nodes split by delimiter `:`. Where `controller` means any of nodes
    with such name, while `controller-0` is just that specific node.

    Example::

       --resource-class-override name=baremetal-ctr,flavor=controller,node=controller
       --resource-class-override name=baremetal-cmp,flavor=compute,node=compute-0
       --resource-class-override name=baremetal-other,flavor=compute,node=swift-0:baremetal

Tripleo Heat Templates configuration options
--------------------------------------------
* ``--config-heat``: Inject additional Tripleo Heat Templates configuration options under "paramater_defaults"
    entry point. Example:

    .. code-block:: shell

       --config-heat ComputeExtraConfig.nova::allow_resize_to_same_host=true
       --config-heat NeutronOVSFirewallDriver=openvswitch

    should inject the following yaml to "overcloud deploy" command:

    .. code-block:: yaml

       ---
       parameter_defaults:
          ComputeExtraConfig:
              nova::allow_resize_to_same_host: true
          NeutronOVSFirewallDriver: openvswitch

    It is also possible to have . (dot) included in key by escaping it:

    .. code-block:: shell

        --config-heat "ControllerExtraConfig.opendaylight::log_levels.org\.opendaylight\.netvirt\.elan=TRACE"

    should inject the following yaml to "overcloud deploy" command:

    .. code-block:: yaml
        ---
        parameter_defaults:
            ControllerExtraConfig:
                opendaylight::log_levels:
                    org.opendaylight.netvirt.elan: TRACE

* ``--config-resource``: Inject additional Tripleo Heat Templates configuration options under "resource_registry"
    entry point. Example:

    .. code-block:: shell

       --config-resource OS::TripleO::BlockStorage::Net::SoftwareConfig=/home/stack/nic-configs/cinder-storage.yaml

    should inject the following yaml to "overcloud deploy" command:

    .. code-block:: yaml

       ---
       resource_registry:
           OS::TripleO::BlockStorage::Net::SoftwareConfig: /home/stack/nic-configs/cinder-storage.yaml

Controlling Node Placement
--------------------------
The default behavior for the director is to randomly select nodes for each role, usually based on their profile tag.
However, the director provides the ability to define specific node placement. This is a useful method to:

    * Assign specific node IDs
    * Assign custom hostnames
    * Assign specific IP addresses

`Cookbook <control_placement.html>`_ example

.. note:: Options are supported for OSP10+

* ``--specific-node-ids``: Bool. Default tagging behaviour is to set properties/capabilities profile, which is based
    on the node_type for all nodes from this type. If this value is set to true/yes, default behaviour will be
    overwritten and profile will be removed, node id will be added to properties/capabilities and scheduler hints
    will be generated. Examples of node IDs include controller-0, controller-1, compute-0, compute-1, and so forth.

* ``--custom-hostnames``: Option to provide custom Hostnames for the nodes. Custom hostnames can be provided
    as values or a env file. Examples:

    .. code-block:: shell

       --custom-hostnames controller-0=ctr-rack-1-0,compute-0=compute-rack-2-0,ceph-0=ceph-rack-3-0

    .. code-block:: shell

       --custom-hostnames local/path/to/custom_hostnames.yaml

    .. code-block:: yaml

        ---
        parameter_defaults:
            HostnameMap:
                ceph-0: storage-0
                ceph-1: storage-1
                ceph-2: storage-2
                compute-0: novacompute-0
                compute-1: novacompute-1
                controller-0: ctrl-0
                controller-1: ctrl-1
                controller-2: ctrl-2
                networker-0: net-0

    .. warning:: When custom hostnames are used, after Overcloud install, InfraRed inventory will be updated with the new
        nodes names. Original node name will be stored as inventory variable named "original_name". "original_name" can
        be used in playbooks as normal host var.

* ``--predictable-ips``: Bool, assign Overcloud nodes with specific IPs on each network. IPs have to be outside DHCP pools.

    .. warning:: Currently InfraRed only creates template for "resource_registry". Nodes IPs need to be provided
        as user environment template, with option --overcloud-templates.

    Example of the template:

    .. code-block:: yaml

        ---
        parameter_defaults:
            CephStorageIPs:
                storage:
                - 172.16.1.100
                - 172.16.1.101
                - 172.16.1.102
                storage_mgmt:
                - 172.16.3.100
                - 172.16.3.101
                - 172.16.3.102

Overcloud Storage
------------------
* ``--storage-external``: Bool
    If ``no``, the overcloud will deploy and manage the storage nodes.
    If ``yes`` the overcloud will connect to an external, per-existing storage service.
* ``--storage-backend``:
    The type of storage service used as backend.
* ``--storage-config``:
    Storage configuration (YAML) file.

.. _`tripleo-undercloud`: tripleo-undercloud.html
.. _`virsh`: virsh.html
.. _`ovb`: ovb.html

Composable Roles
----------------

InfraRed allows to use custom roles to deploy overcloud. Check the `Composable roles <composable_roles.html>`_ page for details.

Overcloud Upgrade
-----------------
.. warning:: Before Overcloud upgrade you need to perform upgrade of `Undercloud <tripleo-undercloud.html>`_

.. warning:: Upgrading from version 11 to version 12 isn't supported via the tripleo-overcloud plugin anymore. Please
     check the tripleo-upgrade plugin for 11 to 12 `upgrade instructions <tripleo_upgrade.html>`_.

Upgrade will detect Undercloud version and will upgrade Overcloud to the same version.

* ``--upgrade``: Bool
  If `yes`, the overcloud will be upgraded.

Example::

  infrared tripleo-overcloud -v --upgrade yes --deployment-files virt

* ``--build``: target build to upgrade to

* ``--enable-testing-repos``: Let you the option to enable testing/pending repos with rhos-release. Multiple values
    have to be coma separated.
    Examples: ``--enable-testing-repos rhel,extras,ceph`` or ``--enable-testing-repos all``

Example::

  infrared tripleo-overcloud -v --upgrade yes --build 2017-05-30.1 --deployment-files virt

.. note:: Upgrade is assuming that Overcloud Deployment script and files/templates, which were used during the initial
  deployment are available at Undercloud node in home directory of Undercloud user. Deployment script location is
  assumed to be "~/overcloud_deploy.sh"


Overcloud Update
----------------

.. warning:: Before Overcloud update it's recommended to update  `Undercloud <tripleo-undercloud.html>`_

.. warning:: Overcloud Install, Overcloud Update and Overcloud Upgrade are mutually exclusive

.. note:: InfraRed supports minor updates from OpenStack 7

Minor update detects Undercloud's version and updates packages within same version to latest available.

* ``--ocupdate``: Bool
  deprecates: --updateto
  If `yes`, the overcloud will be updated

* ``--build``: target build to update to
  defaults to ``None``, in which case, update is disabled.
  possible values: build-date, ``latest``, ``passed_phase1``, ``z3`` and all other labels supported by ``rhos-release``
  When specified, rhos-release repos would be setup and used for minor updates.

* ``--enable-testing-repos``: Let you the option to enable testing/pending repos with rhos-release. Multiple values
    have to be coma separated.
    Examples: ``--enable-testing-repos rhel,extras,ceph`` or ``--enable-testing-repos all``

Example::

    infrared tripleo-overcloud -v --ocupdate yes --build latest --deployment-files virt

.. note:: Minor update expects that Overcloud Deployment script and files/templates,
  used during the initial deployment, are available at Undercloud node in home directory of Undercloud user.
  Deployment script location is assumed to be "~/overcloud_deploy.sh"

* ``--buildmods``: Let you the option to add flags to rhos-release:

    | ``pin`` - Pin puddle (dereference 'latest' links to prevent content from changing). This flag is selected by default
    | ``flea`` - Enable flea repos.
    | ``unstable`` - This will enable brew repos or poodles (in old releases).
    | ``none`` - Use none of those flags.

 .. note:: ``--buildmods`` flag is for internal Red Hat usage.

Overcloud Reboot
----------------

It is possible to reboot overcloud nodes. This is needed if kernel got updated

* ``--postreboot``: Bool
  If `yes`, reboot overcloud nodes one by one.

Example::

  infrared tripleo-overcloud --deployment-files virt --postreboot yes
  infrared tripleo-overcloud --deployment-files virt --ocupdate yes --build latest --postreboot yes

TLS Everywhere
______________
Setup TLS Everywhere with FreeIPA.

``tls-everywhere``: It will configure overcloud for TLS Everywhere.
