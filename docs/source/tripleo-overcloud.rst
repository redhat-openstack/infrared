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

Upgrade will detect Undercloud version and will upgrade Overcloud to the same version.

* ``--upgrade``: Bool
  If `yes`, the overcloud will be upgraded.

Example::

  infrared tripleo-overcloud -v --upgrade yes --deployment-files virt

* ``--updateto``: target build to upgrade to

Example::

  infrared tripleo-overcloud -v --upgrade yes --updateto 2017-05-30.1 --deployment-files virt

.. note:: Upgrade is assuming that Overcloud Deployment script and files/templates, which were used during the initial
  deployment are available at Undercloud node in home directory of Undercloud user. Deployment script location is
  assumed to be "~/overcloud_deploy.sh"


Overcloud Update
----------------

.. warning:: Before Overcloud update it's recommended to update  `Undercloud <tripleo-undercloud.html>`_

.. note:: InfraRed supports minor updates from OpenStack 9

Minor update detects Undercloud's version and updates packages within same version to latest available.

* ``--updateto``: target build to update to
  defaults to ``None``, in which case, update is disabled.
  possible values: build-date, ``latest``, ``passed_phase1``, ``z3`` and all other labels supported by ``rhos-release``
  When specified, rhos-release repos would be setup and used for minor updates.

Example::

    infrared tripleo-overcloud -v --updateto latest --deployment-files virt

.. note:: Minor update expects that Overcloud Deployment script and files/templates,
  used during the initial deployment, are available at Undercloud node in home directory of Undercloud user.
  Deployment script location is assumed to be "~/overcloud_deploy.sh"

* ``--buildmods``: Let you the option to add flags to rhos-release:

    | ``pin`` - Pin puddle (dereference 'latest' links to prevent content from changing). This flag is selected by default
    | ``flea`` - Enable flea repos.
    | ``unstable`` - This will enable brew repos or poodles (in old releases).
    | ``none`` - Use none of those flags.

 .. note:: ``--buildmods`` flag is for internal Red Hat usage.
