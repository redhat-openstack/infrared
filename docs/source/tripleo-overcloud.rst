TripelO Overcloud
=================

Deploys a Tripleo overcloud from an existing undercloud

Introspection
-------------

* ``--instackenv-file``:
    Path to the instackenv.json configuration file used for introspection.
    For `virsh`_ and `ovb`_ deployment, InfraRed can generate this file automatically.

.. Deployment Files

Overcloud
---------
* ``--overcloud-templates``:
    Add extra environment template files to "overcloud deploy" command
    Format:


    .. code:: yml
       :name: sahara.yml

       ---
       tripleo_heat_templates:
           - /usr/share/openstack-tripleo-heat-templates/environments/services/sahara.yaml

* ``--overcloud-script``:
    Customize the script that will deploy the overcloud.
    A path to a *.sh file containing ``openstack overcloud deploy`` command.
    This is for advance users.

* ``--overcloud-ssl``:
    Boolean. Enable SSL for the overcloud services.

* ``--overcloud-debug``:
    Boolean. Enable debug mode for the overcloud services.

Overcloud Public Network
------------------------
* ``--public-vlan``:
    Set this to "yes" if overcloud's external network is on a VLAN that's unreachable from the
    undercloud. This will configure network access from UnderCloud to overcloud's API/External(floating ips)
    network, creating a new VLAN interface connected to ovs's ``br-ctlplane`` bridge.
    |NOTE: If your UnderCloud's network is already configured properly, this could disrupt it, making overcloud API unreachable
    For more details, see:
    `VALIDATING THE OVERCLOUD <https://access.redhat.com/documentation/en/red-hat-openstack-platform/10-beta/paged/director-installation-and-usage/chapter-6-performing-tasks-after-overcloud-creation>`_



.. _`tripleo-undercloud`: tripleo-undercloud.html
.. _`virsh`: virsh.html
.. _`ovb`: missing
