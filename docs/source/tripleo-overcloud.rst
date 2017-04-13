TripleO Overcloud
=================

Deploys a Tripleo overcloud from an existing undercloud

Stages Control
--------------

Run is broken into the following stages. Omitting any of the flags (or setting it to ``no``) will skip that stage

* ``--introspect`` the overcloud nodes
* ``--tag`` overcloud nodes with proper flavors
* ``--deploy`` overcloud of given ``--version``(see below)
* Execute ``--post`` installation steps (like creating a public network - see below)

Deployment Description
----------------------

* ``--deployment-files``: Mandatory.
    Path to a directory, containing heat-templates describing the overcloud deployment.
    Choose ``virt`` to enable preset templates for virtual POC environment (`virsh`_ or `ovb`_).
* ``--instackenv-file``:
    Path to the instackenv.json configuration file used for introspection.
    For `virsh`_ and `ovb`_ deployment, `infrared` can generate this file automatically.
* ``--version``: Tripleo release to install.
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

* ``--overcloud-templates``: Add extra environment template files to "overcloud deploy" command
    Format:

    .. code-block:: plain
       :caption: sahara.yml

       ---
       tripleo_heat_templates:
           - /usr/share/openstack-tripleo-heat-templates/environments/services/sahara.yaml

* ``--overcloud-script``: Customize the script that will deploy the overcloud.
    A path to a *.sh file containing ``openstack overcloud deploy`` command.
    This is for advance users.


Overcloud Public Network
------------------------
* ``--public-network``: Bool. Whether to have `infrared` create a public network on the overcloud.
* ``--public-subnet``:
    Path to file containing different values for the subnet of the network above.
* ``--public-vlan``:
    Set this to "yes" if overcloud's external network is on a VLAN that's unreachable from the
    undercloud. This will configure network access from UnderCloud to overcloud's API/External(floating ips)
    network, creating a new VLAN interface connected to ovs's ``br-ctlplane`` bridge.
    |NOTE: If your UnderCloud's network is already configured properly, this could disrupt it, making overcloud API unreachable
    For more details, see:
    `VALIDATING THE OVERCLOUD <https://access.redhat.com/documentation/en/red-hat-openstack-platform/10-beta/paged/director-installation-and-usage/chapter-6-performing-tasks-after-overcloud-creation>`_

Overcloud Strorage
------------------
* ``--storage-external``: Bool
    If `no`, the overcloud will deploy and manage the storage nodes.
    |If `yes` the overcloud will connect to an external, per-existing storage service.
* ``--storage-backend``:
    The type of the storage service used as backend.
* ``--storage-config``:
    Storage configuration (YAML) file.

.. _`tripleo-undercloud`: tripleo-undercloud.html
.. _`virsh`: virsh.html
.. _`ovb`: missing

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

  infrared tripleo-overcloud -v --upgrade yes  --deployment-files virt

.. note:: Upgrade is assuming that Overcloud Deployment script and files/templates, which were used during the initial
  deployment are available at Undercloud node in home directory of Undercloud user. Deployment script location is
  assumed to be "~/overcloud_deploy.sh"
