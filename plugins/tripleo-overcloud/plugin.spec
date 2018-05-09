---
config:
    plugin_type: install
subparsers:
    tripleo-overcloud:
        description: Install a TripleO overcloud using a designated undercloud node
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Stages Control
              options:
                  introspect:
                      type: Bool
                      help: Specifies whether to run introspection
                      default: False

                  tagging:
                      type: Bool
                      help: Specifies whether to create flavors automatically and tag our hosts with them
                      default: False

                  deploy:
                      type: Bool
                      help: Specifies whether to deploy the overcloud
                      default: False

                  post:
                      type: Bool
                      help: Specifies whether we should run post install tasks
                      default: False

                  pre:
                      type: Bool
                      help: Specifies whether we should run pre install tasks
                      default: False

            - title: Containers
              options:
                  containers:
                      type: Bool
                      help: |
                          Specifies whether the containers should be used for deployment.
                          Infrared will use containers only when install version >= 12
                      default: yes

                  container-images-patch:
                      type: Value
                      help: |
                            Comma,separated list of docker container images to patch using '/patched_rpm' yum repository.
                            NOTE: Patching involves 'yum update' inside the container. This feature is not supported when
                            registry-undercloud-skip is set to True.
                            Also, if this option is not specified, InfraRed auto discovers images that should be updated.
                            This option may be used to patch only a specific container image(s) without updating others that
                            would normally be patched.
                            Example:
                                --container-images-patch openstack-opendaylight,openstack-nova-compute

                  container-images-packages:
                      type: IniType
                      action: append
                      help: |
                            'imagename=package1{,package2}' pairs to install package(s) from URL(s) in the container image
                            before overcloud is deployed. Container images don't have any yum repositories enabled by
                            default hence specifying a location in a form of URL to the RPM to install is mandatory.
                            This option can be used multiple times for different container images. This feature is
                            not supported when registry-undercloud-skip is set to True.
                            NOTE: Only specified image(s) will get the packages installed. All images that depend on
                            updated image have to be updated as well (using this option or otherwise).
                            Example:
                                --container-images-packages openstack-opendaylight=https://kojipkgs.fedoraproject.org//packages/tmux/2.5/3.fc27/x86_64/tmux-2.5-3.fc27.x86_64.rpm,https://kojipkgs.fedoraproject.org//packages/vim/8.0.844/2.fc27/x86_64/vim-minimal-8.0.844-2.fc27.x86_64.rpm

                  registry-mirror:
                      type: Value
                      help: The alternative docker registry to use for deployment.
                      required_when: "registry-skip-puddle == True"

                  registry-undercloud-skip:
                      type: Bool
                      help: Avoid using and mass populating the undercloud registry.
                            The registry or the registry-mirror will be used directly when possible,
                            recommended to use this option when you have very good bandwidth to your registry.
                      default: False

                  registry-skip-puddle:
                      type: Bool
                      help: Skip reading any private puddle files to auto-detect the containers parameters
                      default: False

                  registry-namespace:
                      type: Value
                      help: The alternative docker registry namespace to use for deployment.

                  registry-prefix:
                      type: Value
                      help: The images prefix

                  registry-tag:
                      type: Value
                      help: The images tag
                      required_when: "registry-skip-puddle == True"

                  registry-tag-label:
                      type: Value
                      help: |
                          If this option is set then infrared will try to get
                          tag hash using the openstack overcloud container image tag discover
                          command
                  registry-tag-image:
                      type: Value
                      help: |
                          The image to use to read the tab hash

                  registry-ceph-namespace:
                      type: Value
                      help: namesapce for the ceph container

                  registry-ceph-image:
                      type: Value
                      help: image for the ceph container

                  registry-ceph-tag:
                      type: Value
                      help: tag used with the ceph container
                      default: latest

            - title: Deployment Description
              options:
                  version:
                      type: Value
                      help: |
                          The product version
                          Numbers are for OSP releases
                          Names are for RDO releases
                          If not given, same version of the undercloud will be used
                      choices:
                        - "7"
                        - "8"
                        - "9"
                        - "10"
                        - "11"
                        - "12"
                        - "13"
                        - "14"
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                        - pike
                        - queens
                        - rocky

                  deployment-files:
                      type: VarDir
                      help: |
                          The absolute path to the folder containing the templates of the overcloud deployment.
                          Please see `settings/installer/ospd/deployment/example` as reference.
                          Use "virt" to enable preset templates for virtual POC environment.
                      required: yes

                  deployment-timeout:
                      type: int
                      help: The overcloud deployment timeout in minutes.
                      default: 100
                      maximum: 180

                  instackenv-file:
                      type: Value
                      help: The path to the instackenv.json configuration file used for introspection.

                  controller-nodes:
                      type: Value
                      help: The amount of controller nodes to deploy

                  compute-nodes:
                      type: Value
                      help: The amount of compute nodes to deploy

                  storage-nodes:
                      type: Value
                      help: |
                            The amount of storage nodes to deploy. If --storage-backend is set, this
                            value will default to '1', otherwise no storage nodes will be used.

                  ntp-server:
                      type: Value
                      help: |
                            Ntp server name (or IP) to use.
                      default: clock.redhat.com

                  hybrid:
                      type: FileValue
                      help: |
                            Specifies whether deploying a hybrid environment.
                            The target file should contains information about the bare-metals servers
                            that will be added to the instackenv.json file during introspection.

                  environment-plan:
                      type: Value
                      short: p
                      help: |
                            The absolute path or url address to a custom environment plan file.
                            Environment plan file example:
                              tripleo-overcloud/vars/environment/plan/example.yml
                            NOTE: Infrared support this option for RHOSP from version 12.

                  libvirt-type:
                      type: Value
                      help: The libvirt type to use during the overcloud deployment
                      default: kvm
                      choices:
                          - kvm
                          - qemu

            - title: Overcloud Options
              options:
                  overcloud-debug:
                      type: Bool
                      default: yes
                      help: Specifies whether overcloud service should enable debug mode

                  overcloud-ssl:
                      type: Bool
                      default: no
                      help: Specifies whether ths SSL should be used for overcloud

                  overcloud-script:
                      type: Value
                      help: |
                            The absolute path to a custom overcloud deployment script.
                            If not set, it will auto generate a deployment according to the
                            provided templates / options.

                  overcloud-templates:
                      type: ListOfVarFiles
                      help: |
                            Add extra environment template files to "overcloud deploy" command
                            File (in YAML format) containing a list of paths to template files on the UnderCloud.
                            NOTE: Omit this to not include any extra files, or use "none"
                            __LISTYAMLS__

                  config-heat:
                      type: NestedDict
                      action: append
                      help: |
                          Inject additional Tripleo Heat Templates configuration options under "paramater_defaults"
                          entry point.
                          Example:
                              --config-heat ComputeExtraConfig.nova::allow_resize_to_same_host=true
                              --config-heat NeutronOVSFirewallDriver=openvswitch
                          should inject the following yaml to "overcloud deploy" command:

                              ---
                              parameter_defaults:
                                  ComputeExtraConfig:
                                      nova::allow_resize_to_same_host: true
                                  NeutronOVSFirewallDriver: openvswitch

                  config-resource:
                      type: NestedDict
                      action: append
                      help: |
                          Inject additional Tripleo Heat Templates configuration options under "resource_registry"
                          entry point.
                          Example:
                              --config-resource OS::TripleO::BlockStorage::Net::SoftwareConfig=/home/stack/nic-configs/cinder-storage.yaml
                          should inject the following yaml to "overcloud deploy" command:

                              ---
                              resource_registry:
                                  OS::TripleO::BlockStorage::Net::SoftwareConfig: /home/stack/nic-configs/cinder-storage.yaml

                  extra-deploy-params:
                      type: Value
                      help: |
                          Extra parameters to append to 'openstack overcloud deploy' command.
                          NOTE: Using equal(=) sign is mandatory here.
                          Example:
                              --extra-deploy-params="--config-download"

                  heat-templates-basedir:
                      type: Value
                      help: Overrides the templates base dir for the overcloud deploy script.
                      default: "/usr/share/openstack-tripleo-heat-templates"

                  overcloud-stack:
                      type: Value
                      help: Overrides the overcloud stack name
                      default: "overcloud"

                  overcloud-ssh-user:
                      type: Value
                      help: Overrides the overcloud ssh user name
                      default: ''

                  tls-everywhere:
                      type: Bool
                      help: |
                          Specifies whether TLS Everywhere with FreeIPA should be implemented
                      default: no

            - title: Network Configuration
              options:
                  network-backend:
                      type: Value
                      help: The overcloud network backend.
                      default: vxlan

                  network-protocol:
                      type: Value
                      help: The overcloud network backend.
                      default: ipv4
                      choices:
                          - ipv4
                          - ipv6

                  network-lbaas:
                      type: Bool
                      default: no
                      help: Activate Neutron LBaaS(v2) extension on the overcloud.

                  network-bgpvpn:
                      type: Bool
                      default: no
                      help: APIs and framework to attach BGP VPNs to Neutron networks

                  network-dvr:
                      type: Bool
                      default: no
                      help: Activate Neutron DVR extension on the overcloud.

                  network-l2gw:
                      type: Bool
                      default: no
                      help: Activate APIs and implementations to support L2 Gateways in Neutron

                  network-octavia:
                      type: Bool
                      default: no
                      help: Deploy Overcloud with Octavia (Load Balancer).

                  network-lbaas:
                      type: Bool
                      default: no
                      help: Deploy Overcloud with LBaaS v2. (OSP >= 13, RDO >= Queens)

                  network-ovn:
                      type: Bool
                      default: no
                      help: Use OVN (HA) instead of ML2 and OVS.

            - title: Overcloud Public Network
              options:
                  public-network:
                      type: Bool
                      default: yes
                      help: Deploy "public" external network on the overcloud as post-install.

                  public-net-name:
                      type: Value
                      help: |
                          Specifies the name of the public network.
                          NOTE: If not provided it will use the default one for the OSP version

                  public-subnet:
                      type: VarFile
                      help: |
                          Subnet detail for "public" external network on the overcloud as post-install.
                          (CIDR, Allocation Pool, Gateway)
                          __LISTYAMLS__
                      default: default_subnet

                  public-vlan-ip:
                      type: Value
                      help: |
                          Provide IP address from the external network range for the Undercloud host.
                          NOTE: The address should be excluded from the external_api pool within the network-envornment.yaml file.
                          Provide the IP address if overcloud's external ("public") network is on a VLAN that's unreachable from the
                          Undercloud.
                          This will configure network access from UnderCloud to overcloud's API/External(floating ips)
                          network, creating a new VLAN interface connected to ovs's "br-ctlplane" bridge.
                          NOTE: If your UnderCloud's network is already configured properly, this could disrupt it, making overcloud API unreachable
                          For more details, see: "VALIDATING THE OVERCLOUD" on https://access.redhat.com/documentation/en/red-hat-openstack-platform/10-beta/paged/director-installation-and-usage/chapter-6-performing-tasks-after-overcloud-creation
                  external-vlan:
                      type: Value
                      help: |
                         An Optional external VLAN ID of the external network (Not to be confused with the Public API network)

            - title: Overcloud storage
              options:
                  storage-external:
                      type: Bool
                      help: Whether to use an external storage rather than setting it up with the director
                      default: no

                  storage-method:
                      type: Value
                      choices:
                          - puppet
                          - ansible
                      help: |
                        Selecting deploy method when multiple method is possible.
                        Today this option is only used when the openetsk version is pike or newer and
                        the storage-external is yes/true, but it can be extended in the future.
                        Default behavior depends on the OpenStack version.
                  storage-backend:
                      type: Value
                      choices:
                          - ceph
                          - swift
                          - netapp-iscsi
                          - netapp-nfs
                          - lvm
                      help: |
                        The storage that we would like to use.
                        If not supplied, Infrared will try to discover storage nodes and select appropriate backed.
                        The 'lvm' value will be used when storage nodes were not found.
                        NOTE: when not using external storage, this will set the default for "--storage-nodes" to 1.

                  storage-config:
                      type: Value
                      help: |
                          Storage configuration file (YAML file)
                          __LISTYAMLS__
                      default: internal

            - title: Composable roles
              options:
                  role-files:
                      type: Value
                      help: |
                        For the OSP11 and below:
                        Specifies a sub-folder under the files/roles/ folder where InfraRed should look for the roles files.
                        InfraRed will use the composable roles approach when this flag is defined

                        For the OSP12 and above:
                        Specifies the list of roles from https://github.com/openstack/tripleo-heat-templates/tree/master/roles
                        to use. For example, for the controller,compute and ceph topology the following value can be used:
                         --role-files=Controller,Compute,CephStorage.
                         If that value is equal to 'auto' or is not a list of roles, then Infrared will try to
                         automatically discover roles to use.
                  tht-roles:
                      type: Bool
                      default: yes
                      help: |
                        Specifies whether the THT(https://github.com/openstack/tripleo-heat-templates/tree/master/roles)
                        roles should be used for OSP12+ composable deployments. If value is 'no', then the OSP11 approach
                        will be used.

            - title: Control Node Placement
              options:
                  specific-node-ids:
                      type: Bool
                      default: no
                      help: |
                          Default tagging behaviour is to set properties/capabilities profile, which is based on the
                          node_type for all nodes from this type. If this value is set to true/yes, default behaviour
                          will be overwritten and profile will be removed, node id will be added to properties/capabilities
                          and scheduler hints will be generated.
                          Examples of node IDs include controller-0, controller-1, compute-0, compute-1, and so forth.

                  custom-hostnames:
                      type: Value
                      help: |
                          Option to provide custom Hostnames for the nodes.
                          Note: Custom hostnames can be provided as values or a env file.
                          Value example:
                          --custom-hostnames controller-0=ctr-rack-1-0,compute-0=compute-rack-2-0,ceph-0=ceph-rack-3-0
                          File example:
                          --custom-hostnames local/path/to/custom_hostnames.yaml

                  predictable-ips:
                      type: Bool
                      default: no
                      help: |
                          Assign Overcloud nodes with specific IPs on each network. IPs are outside DHCP pools.
                          Note: Currently InfraRed only creates template for "resource_registry". Nodes IPs need
                          to be provided as user environment template, with option --overcloud-templates

            - title: Splitstack deployment
              options:
                  splitstack:
                      type: Bool
                      default: no
                      help: |
                        If customer has already provisioned nodes for an overcloud splitstack should be used to utilize these
                        nodes.(https://access.redhat.com/documentation/en-us/red_hat_openstack_platform/11/html/director_installation_and_usage/chap-configuring_basic_overcloud_requirements_on_pre_provisioned_nodes)

            - title: Overcloud Upgrade
              options:
                  upgrade:
                      type: Bool
                      help: |
                          Upgrade Overcloud.
                          NOTE: Upgrade require overcloud deployment script to be available in home directory of undercloud
                          user at undercloud node
                          Currently, there is upgrade possibility from version 9 to version 10 only.
                  mirror:
                      type: Value
                      help: |
                          Enable usage of specified mirror (for rpm, pip etc) [brq,qeos,tlv - or hostname].
                          (Specified mirror needs to proxy multiple rpm source hosts and pypi packages.)
                  updateto:
                      type: Value
                      help: |
                          Deprecated argument. Please use 'ocupdate' argument
                      default: None
                  ocupdate:
                      deprecates: updateto
                      type: Bool
                      help: |
                          Perform minor update of overcloud.
                          NOTE: Currently, minor update is supported with IR just for versions > 6.
                      default: False
                  director-build:
                      help: |
                          String represents a timestamp of the OSP director puddle
                          (for the given product core version). Only applies for
                          6 < OSPd < 10, and could be used with '--build' flag.
                          Note: for versions >= 10 only the --build flag should be used to
                          specify a puddle.
                          Supports any rhos-release labels.
                          Examples: "passed_phase1", "2016-08-11.1", "Y1", "Z3", "GA"
                          If missing, will equal to "latest".
                      type: Value
                      default: latest
                  build:
                     type: Value
                     help: |
                          In conjunction with '--ocupdate' or '--upgrade' specifies the build which to use.
                          When omitted with update/upgrade - uses 'latest'.
                     default: None
                  osrelease:
                      type: Value
                      help: |
                          Override the default RHEL version. Default 'ansible_distribution_version'
                  buildmods:
                      type: Value
                      help: |
                          List of flags for rhos-release module.
                          Currently works with
                          pin - pin puddle (dereference 'latest' links to prevent content from changing)
                          flea - enable flea repos
                          unstable - this will enable brew repos or poodles (in old releases)
                          cdn - use internal mirrors of the CDN repos. (internal use)
                          none - use none of those flags
                      default: pin
                  enable-testing-repos:
                      type: Value
                      help: |
                          Let you the option to enable testing/pending repos with rhos-release. Multiple values have to be coma separated.
                          Examples: --enable-testing-repos rhel,extras,ceph or --enable-testing-repos all
                  postreboot:
                      type: Bool
                      help: |
                          Reboot overcloud nodes one-by-one. By default don't reboot.
                          Useful with '--ocupdate' to reboot nodes after minor update,
                          or with '--deploy' to reboot after oc is deployed.
                      default: False
                  postreboot_evacuate:
                      type: Bool
                      help: |
                          Live migrate instances before rebooting compute nodes and migrate them back after
                          the node boots.
                      default: False
                  dataplaneping:
                      type: Bool
                      help: |
                          Validate connectivity to floating IP doesn't get interrupted during update/upgrade.
                      default: False

            - title: Ironic Configuration
              options:
                  vbmc-username:
                      type: Value
                      default: admin
                      help: |
                          VBMC username (Relevant when Ironic's driver is 'pxe_ipmitool' - OSP >= 11)
                          NOTE: If you use non default value for the option, and you execute introspection
                          and deploy (--introspect yes/--deploy yes) in different IR runs, you need to provide
                          the option on both runs.
                  vbmc-password:
                      type: Value
                      default: password
                      help: |
                          VBMC password (Relevant when Ironic's driver is 'pxe_ipmitool' - OSP >= 11)
                          NOTE: If you use non default value for the option, and you execute introspection
                          and deploy (--introspect yes/--deploy yes) in different IR runs, you need to provide
                          the option on both runs.
                  vbmc-host:
                      type: Value
                      default: hypervisor
                      choices:
                          - "hypervisor"
                          - "undercloud"
                      help: |
                          Specifies on what server the virtualbmc service should be installed.
                          NOTE: If you use non default value for the option, and you execute introspection
                          and deploy (--introspect yes/--deploy yes) in different IR runs, you need to provide
                          the option on both runs.
                  vbmc-force:
                      type: Bool
                      default: False
                      help: |
                          Specifies whether the vbmc (pxe_ipmitool ironic driver) should be used for
                          the OSP10 and below.
                          NOTE: If you use non default value for the option, and you execute introspection
                          and deploy (--introspect yes/--deploy yes) in different IR runs, you need to provide
                          the option on both runs.
                  resource-class-enabled:
                      type: Bool
                      default: True
                      help: |
                          Scheduling based on resource classes, a Compute service flavor is able to use the
                          node’s resource_class field (available starting with Bare Metal API version 1.21)
                          for scheduling, instead of the CPU, RAM, and disk properties defined in the flavor.
                          A flavor can request exactly one instance of a bare metal resource class.
                          (https://docs.openstack.org/ironic/latest/install/configure-nova-flavors.html#scheduling-based-on-resource-classes)
                          Scheduling based on resource classes is enabled by default if OSP>=12. This option
                          allows to disable it.
                          Example: --resource-class-enabled False
                  resource-class-override:
                      type: NestedList
                      action: append
                      help: |
                          This option allows to create custom resource class and tie it to flavor and instances.
                          The 'node' field supports 'controller' or 'controller-0' patterns.
                          Example:
                              --resource-class-override name=baremetal-ctr,flavor=controller,node=controller
                              --resource-class-override name=baremetal-cmp,flavor=compute,node=compute-0
                              --resource-class-override name=baremetal-other,flavor=compute,node=swift-0:baremetal

            - title: ansible facts
              options:
                  collect-ansible-facts:
                      type: Bool
                      help: Save ansible facts as json file(s)
                      default: False
