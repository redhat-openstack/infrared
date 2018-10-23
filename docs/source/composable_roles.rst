Composable Roles
----------------

InfraRed allows to define `Composable Roles <https://access.redhat.com/documentation/en-us/red_hat_openstack_platform/10/html-single/advanced_overcloud_customization/#Roles>`_ while installing OpenStack with tripleo.


Overview
========

To deploy overcloud with the composable roles the additional templates should be provided:
  - nodes template: list all the roles, list of the services for every role. For example::

      - name: ObjectStorage
        CountDefault: 1
        ServicesDefault:
            - OS::TripleO::Services::CACerts
            - OS::TripleO::Services::Kernel
            - OS::TripleO::Services::Ntp
            [...]
        HostnameFormatDefault: swift-%index%

      - name: Controller
        CountDefault: 1
        ServicesDefault:
            - OS::TripleO::Services::CACerts
            - OS::TripleO::Services::CephMon
            - OS::TripleO::Services::CephExternal
            - OS::TripleO::Services::CephRgw
            [...]
        HostnameFormatDefault: controller-%index%

      - name: Compute
        CountDefault: 1
        ServicesDefault:
            - OS::TripleO::Services::CACerts
            - OS::TripleO::Services::CephClient
            - OS::TripleO::Services::CephExternal
            [....]
        HostnameFormatDefault: compute-%index%

      - name: Networker
        CountDefault: 1
        ServicesDefault:
            - OS::TripleO::Services::CACerts
            - OS::TripleO::Services::Kernel
            [...]
        HostnameFormatDefault: networker-%index%

  - template with the information about roles count, flavors and other defaults::

        parameter_defaults:
            ObjectStorageCount: 1
            OvercloudSwiftStorageFlavor: swift
            ControllerCount: 2
            OvercloudControlFlavor: controller
            ComputeCount: 1
            OvercloudComputeFlavor: compute
            NetworkerCount: 1
            OvercloudNetworkerFlavor: networker
            [...]

  - template with the information about roles resources (usually network and port resources)::

        resource_registry:
            OS::TripleO::ObjectStorage::Net::SoftwareConfig: /home/stack/deployment_files/network/nic-configs/osp11/swift-storage.yaml
            OS::TripleO::Controller::Net::SoftwareConfig: /home/stack/deployment_files/network/nic-configs/osp11/controller.yaml
            OS::TripleO::Compute::Net::SoftwareConfig: /home/stack/deployment_files/network/nic-configs/osp11/compute.yaml
            OS::TripleO::Networker::Ports::TenantPort: /usr/share/openstack-tripleo-heat-templates/network/ports/tenant.yaml
            OS::TripleO::Networker::Ports::InternalApiPort: /usr/share/openstack-tripleo-heat-templates/network/ports/internal_api.yaml
            OS::TripleO::Networker::Net::SoftwareConfig: /home/stack/deployment_files/network/nic-configs/osp11/networker.yaml
            [...]

  .. note:: The nic-configs in the infrared deployment folder are stored in two folders (``osp11`` and ``legacy``) depending on the product version installed.



InfraRed allows to simplify the process of templates generation and auto-populates the roles according to the deployed topology.


Defining topology and roles
===========================

Deployment approaches with composable roles differ for OSP11 and OSP12+ products.

For OSP11 user should manually compose all the roles templates and provide them to the deploy script.
For OSP12 and above the tripleo provides the ``openstack overcloud roles generate`` command to automatically generate roles templates.
See `THT roles`_ for more information about tripleo roles.

OSP12 Deployment
^^^^^^^^^^^^^^^^

The Infrared provides there options to deploy openstack with composable roles in OSP12+.

**1) Automatically discover roles from the inventory.** In that case Inrared tries to determine what roles should be used basing
on the list of the ``overcloud_nodes`` from the inventory file. To enable automatic roles discover the ``--role-files``
option should be set to ``auto`` or any other non-list value (not separated with ','). For example::

    # provision
    ir virsh -vvvv
        --topology-nodes=undercloud:1,controller:2,compute:1,networker:1,swift:1 \
        --host-address=seal52.qa.lab.tlv.redhat.com \
        --host-key ~/.ssh/my-prov-key

    # do undercloud install [...]

    # overcloud
    ir tripleo-overcloud -vvvv
        --version=12 \
        --deploy=yes \
        --role-files=auto \
        --deployment-files=composable_roles \
        [...]


**2) Manually specify roles to use.** In that case user can specify the list roles to use by setting the ``--role-files`` otion
to the list of roles from the `THT roles`_::

    # provision
    ir virsh -vvvv
        --topology-nodes=undercloud:1,controller:2,compute:1,messaging:1,database:1,networker:1 \
        --host-address=seal52.qa.lab.tlv.redhat.com \
        --host-key ~/.ssh/my-prov-key

    # do undercloud install [...]

    # overcloud
    ir tripleo-overcloud -vvvv
        --version=12 \
        --deploy=yes \
        --role-files=ControllerOpenstack,Compute,Messaging,Database,Networker \
        --deployment-files=composable_roles \
        [...]


**3) User legacy OSP11 approach to generate roles templates.** See detailed desciption below.
To enable that approach the ``--tht-roles`` flag should be set to `no` and the ``--role-files`` should point
to the IR folder with the roles. For example::

    # provision
    ir virsh -vvvv
        --topology-nodes=undercloud:1,controller:2,compute:1,networker:1,swift:1 \
        --host-address=seal52.qa.lab.tlv.redhat.com \
        --host-key ~/.ssh/my-prov-key

    # do undercloud install [...]

    # overcloud
    ir tripleo-overcloud -vvvv
        --version=12 \
        --deploy=yes \
        --role-files=networker \
        --tht-roles=no \
        --deployment-files=composable_roles \
        [...]


.. _THT roles: https://github.com/openstack/tripleo-heat-templates/tree/master/roles

OSP11 Deployment
^^^^^^^^^^^^^^^^

To deploy custom roles, InfraRed should know what nodes should be used for what roles. This involves a 2-step procedure.

**Step #1** Setup available nodes and store them in the InfraRed inventory. Those nodes can be configured by the ``provision`` plugin such as `virsh <virsh.html>`_::

    ir virsh -vvvv
        --topology-nodes=undercloud:1,controller:2,compute:1,networker:1,swift:1 \
        --host-address=seal52.qa.lab.tlv.redhat.com \
        --host-key ~/.ssh/my-prov-key

In that example we defined a ``networker`` nodes which holds all the neutron services.

**Step #2** Provides a path to the roles definition while `installing the overcloud <tripleo-overcloud.html>`_ using the ``--role-files`` option::

    ir tripleo-overcloud -vvvv
        --version=10 \
        --deploy=yes \
        --role-files=networker \
        --deployment-files=composable_roles \
        --introspect=yes \
        --storage-backend=swift \
        --tagging=yes \
        --post=yes

In that example, to build the composable roles templates, InfraRed will look into the ``<plugin_dir>/files/roles/networker`` folder
for the files that corresponds to all the node names defined in the ``inventory->overcloud_nodes`` group.

All those role files hold role parameters. See `Role Description`_ section for details.

When role file is not found in the user specified folder
InfraRed will try to use a ``default`` roles from the ``<plugin_dir>/files/roles/default`` folder.

For the topology described above with the networker custom role the following role files can be defined:
  - <plugin_dir>/files/roles/**networker**/controller.yml - holds controller roles without neutron services
  - <plugin_dir>/files/roles/**networker**/networker.yml - holds the networker role description with the neutron services
  - <plugin_dir>/files/roles/**default**/compute.yml - a default compute role description
  - <plugin_dir>/files/roles/**default**/swift.yml - a default swift role description

To deploy non-supported roles, a new folder should be created in the ``<plugin_dir>/files/roles/``.
Any roles files that differ (e.g. service list) from the defaults should be put there. That folder is then can be referenced with the ``--role-files=<folder name>`` argument.

Role Description
================

All the custom and defaults role descriptions are stored in the ``<plugin_dir>/files/roles`` folder.
Every role file holds the following information:

  - ``name`` - name of the role
  - ``resource_registry`` - all the resources required for a role.
  - ``flavor`` - the flavor to use for a role
  - ``host_name_format`` - the resulting host name format for the role node
  - ``services`` - the list of services the role holds

Below is an example of the controller default role::

    controller_role:
        name: Controller

        # the primary role will be listed first in the roles_data.yaml template file.
        primary_role: yes

        # include resources
        # the following vars can be used here:
        #  - ${ipv6_postfix}: will be replaced with _v6 when the ipv6 protocol is used for installation, otherwise is empty
        #  - ${deployment_dir} - will be replaced by the deployment folder location on the undercloud. Deployment folder can be specified with the ospd --deployment flag
        #  - ${nics_subfolder} - will be replaced by the appropriate subfolder with the nic-config's. The subfolder value
        #        is dependent on the product version installed.
        resource_registry:
            "OS::TripleO::Controller::Net::SoftwareConfig": "${deployment_dir}/network/nic-configs/${nics_subfolder}/controller${ipv6_postfix}.yaml"
        # required to support OSP12 deployments
        networks:
            - External
            - InternalApi
            - Storage
            - StorageMgmt
            - Tenant
        # we can also set a specific flavor for a role.
        flavor: controller
        host_name_format: 'controller-%index%'

        # condition can be used to include or disable services. For example:
        #  - "{% if install.version |openstack_release < 11 %}OS::TripleO::Services::VipHosts{% endif %}"
        services:
            - OS::TripleO::Services::CACerts
            - OS::TripleO::Services::CephClient
            - OS::TripleO::Services::CephExternal
            - OS::TripleO::Services::CephRgw
            - OS::TripleO::Services::CinderApi
            - OS::TripleO::Services::CinderBackup
            - OS::TripleO::Services::CinderScheduler
            - OS::TripleO::Services::CinderVolume
            - OS::TripleO::Services::Core
            - OS::TripleO::Services::Kernel
            - OS::TripleO::Services::Keystone
            - OS::TripleO::Services::GlanceApi
            - OS::TripleO::Services::GlanceRegistry
            - OS::TripleO::Services::HeatApi
            - OS::TripleO::Services::HeatApiCfn
            - OS::TripleO::Services::HeatApiCloudwatch
            - OS::TripleO::Services::HeatEngine
            - OS::TripleO::Services::MySQL
            - OS::TripleO::Services::NeutronDhcpAgent
            - OS::TripleO::Services::NeutronL3Agent
            - OS::TripleO::Services::NeutronMetadataAgent
            - OS::TripleO::Services::NeutronApi
            - OS::TripleO::Services::NeutronCorePlugin
            - OS::TripleO::Services::NeutronOvsAgent
            - OS::TripleO::Services::RabbitMQ
            - OS::TripleO::Services::HAproxy
            - OS::TripleO::Services::Keepalived
            - OS::TripleO::Services::Memcached
            - OS::TripleO::Services::Pacemaker
            - OS::TripleO::Services::Redis
            - OS::TripleO::Services::NovaConductor
            - OS::TripleO::Services::MongoDb
            - OS::TripleO::Services::NovaApi
            - OS::TripleO::Services::NovaMetadata
            - OS::TripleO::Services::NovaScheduler
            - OS::TripleO::Services::NovaConsoleauth
            - OS::TripleO::Services::NovaVncProxy
            - OS::TripleO::Services::Ntp
            - OS::TripleO::Services::SwiftProxy
            - OS::TripleO::Services::SwiftStorage
            - OS::TripleO::Services::SwiftRingBuilder
            - OS::TripleO::Services::Snmp
            - OS::TripleO::Services::Timezone
            - OS::TripleO::Services::CeilometerApi
            - OS::TripleO::Services::CeilometerCollector
            - OS::TripleO::Services::CeilometerExpirer
            - OS::TripleO::Services::CeilometerAgentCentral
            - OS::TripleO::Services::CeilometerAgentNotification
            - OS::TripleO::Services::Horizon
            - OS::TripleO::Services::GnocchiApi
            - OS::TripleO::Services::GnocchiMetricd
            - OS::TripleO::Services::GnocchiStatsd
            - OS::TripleO::Services::ManilaApi
            - OS::TripleO::Services::ManilaScheduler
            - OS::TripleO::Services::ManilaBackendGeneric
            - OS::TripleO::Services::ManilaBackendNetapp
            - OS::TripleO::Services::ManilaBackendCephFs
            - OS::TripleO::Services::ManilaShare
            - OS::TripleO::Services::AodhApi
            - OS::TripleO::Services::AodhEvaluator
            - OS::TripleO::Services::AodhNotifier
            - OS::TripleO::Services::AodhListener
            - OS::TripleO::Services::SaharaApi
            - OS::TripleO::Services::SaharaEngine
            - OS::TripleO::Services::IronicApi
            - OS::TripleO::Services::IronicConductor
            - OS::TripleO::Services::NovaIronic
            - OS::TripleO::Services::TripleoPackages
            - OS::TripleO::Services::TripleoFirewall
            - OS::TripleO::Services::OpenDaylightApi
            - OS::TripleO::Services::OpenDaylightOvs
            - OS::TripleO::Services::SensuClient
            - OS::TripleO::Services::FluentdClient
            - OS::TripleO::Services::VipHosts

The name of the role files should correspond to the node inventory name without prefix and index.
For example, for ``user-prefix-controller-0`` the name of the role should be ``controller.yml``.

OSP11 Deployment example
=========================

To deploy OpenStack with composable roles on virtual environment the following steps can be performed.

1) Provision all the required virtual machines on a hypervizor with the virsh plugin::

    infrared virsh -vv \
        -o provision.yml \
        --topology-nodes undercloud:1,controller:3,db:3,messaging:3,networker:2,compute:1,ceph:1  \
        --host-address my.host.redhat.com \
        --host-key /path/to/host/key \
        -e override.controller.cpu=8 \
        -e override.controller.memory=32768

2) Install undercloud and overcloud images::

    infrared tripleo-undercloud -vv -o install.yml \
        -o undercloud-install.yml \
        --version 11 \
        --images-task rpm

3) Install overcloud::

     infrared tripleo-overcloud -vv \
         -o overcloud-install.yml \
         --version 11 \
         --role-files=composition \
         --deployment-files composable_roles \
         --introspect yes \
         --tagging yes \
         --deploy yes

     infrared cloud-config -vv \
     -o cloud-config.yml \
     --deployment-files virt \
     --tasks create_external_network,forward_overcloud_dashboard,network_time,tempest_deployer_input

