TripleO Overcloud
=================

Deploys a TripleO overcloud from an existing undercloud

Stages Control
--------------

Run is broken into the following stages. Omitting any of the flags (or setting it to ``no``) will skip that stage

* ``--introspect`` the overcloud nodes
* ``--tag`` overcloud nodes with proper flavors
* ``--deploy`` overcloud of given ``--version`` (see below)
* Execute ``--post`` installation steps (like creating a public network - see below)

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

    .. code-block:: plain
       :caption: sahara.yml

       ---
       tripleo_heat_templates:
           - /usr/share/openstack-tripleo-heat-templates/environments/services/sahara.yaml

    .. code-block:: plain
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

Tripleo Heat Templates configuration options
--------------------------------------------
* ``--config-heat``: Inject additional Tripleo Heat Templates configuration options under "paramater_defaults"
    entry point. Example:

    .. code-block:: plain

       --config-heat ComputeExtraConfig.nova::allow_resize_to_same_host=true
       --config-heat NeutronOVSFirewallDriver=openvswitch

    should inject the following yaml to "overcloud deploy" command:

    .. code-block:: yaml

       ---
       parameter_defaults:
          ComputeExtraConfig:
              nova::allow_resize_to_same_host: true
          NeutronOVSFirewallDriver: openvswitch

Overcloud Public Network
------------------------
* ``--public-network``: Bool. Whether to have `infrared` create a public network on the overcloud.
* ``--public-subnet``:
    Path to file containing different values for the subnet of the network above.
* ``--public-vlan``:
    Set this to ``yes`` if overcloud's external network is on a VLAN that's unreachable from the
    undercloud. This will configure network access from UnderCloud to overcloud's API/External(floating IPs)
    network, creating a new VLAN interface connected to ovs's ``br-ctlplane`` bridge.
    |NOTE: If your UnderCloud's network is already configured properly, this could disrupt it, making overcloud API unreachable
    For more details, see:
    `VALIDATING THE OVERCLOUD <https://access.redhat.com/documentation/en/red-hat-openstack-platform/10-beta/paged/director-installation-and-usage/chapter-6-performing-tasks-after-overcloud-creation>`_

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
     check the tripleo-upgrade plugin for 11 to 12 `upgrade instructions <tripleo_upgrade.html>`

Upgrade will detect Undercloud version and will upgrade Overcloud to the same version.

* ``--upgrade``: Bool
  If `yes`, the overcloud will be upgraded.

Example::

  infrared tripleo-overcloud -v --upgrade yes --deployment-files virt

* ``--build``: target build to upgrade to

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
