---
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

            - title: Containers
              options:
                  containers:
                      type: Bool
                      help: |
                          Specifies whether the containers should be used for deployment.
                          Infrared will use containers only when install version >= 12
                      # todo(obaranov) Change it to yes once containers become more stable
                      default: no

                  registry-mirror:
                      type: Value
                      help: The alternative docker registry to use for deployment.

                  registry-namespace:
                      type: Value
                      help: The alternative docker registry namespace to use for deployment.

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
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                        - pike

                  deployment-files:
                      type: VarDir
                      help: |
                          The absolute path to the folder containing the templates of the overcloud deployment.
                          Please see `settings/installer/ospd/deployment/example` as reference.
                          Use "virt" to enable preset templates for virtual POC environment.
                      required: yes

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

                  heat-templates-basedir:
                      type: Value
                      help: Overrides the templates base dir for the overcloud deploy script.
                      default: "/usr/share/openstack-tripleo-heat-templates"

            - title: Network Configuration
              options:
                  network-backend:
                      type: Value
                      help: The overcloud network backend.
                      choices:
                          - gre
                          - vxlan
                          - vlan
                      default: vxlan

                  network-protocol:
                      type: Value
                      help: The overcloud network backend.
                      default: ipv4
                      choices:
                          - ipv4
                          - ipv6

                  network-mtu:
                      type: Value
                      help: Sets the MTU of the underlying physical network.
                      default: 1500

                  network-lbaas:
                      type: Bool
                      default: no
                      help: Activate Neutron LBaaS(v2) extension on the overcloud.

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

                  network-ovn:
                      type: Bool
                      default: no
                      help: Use OVN instead of ML2 and OVS.

                  octavia-image-url:
                      type: Value
                      help: |
                        URL to the image used for creating the Octavia Amphora node.
                        Default is internal path for RHEL guest image
                      default: https://url.corp.redhat.com/rhel-guest-image-7-3-35-x86-64-qcow2

            - title: Overcloud Public Network
              options:
                  public-network:
                      type: Bool
                      default: yes
                      help: Deploy "public" external network on the overcloud as post-install.

                  public-subnet:
                      type: VarFile
                      help: |
                          Subnet detail for "public" external network on the overcloud as post-install.
                          (CIDR, Allocation Pool, Gateway)
                          __LISTYAMLS__
                      default: default_subnet

                  public-vlan:
                      type: Bool
                      default: no
                      help: |
                          Set this to "yes" if overcloud's external network is on a VLAN that's unreachable from the
                          undercloud.
                          This will configure network access from UnderCloud to overcloud's API/External(floating ips)
                          network, creating a new VLAN interface connected to ovs's "br-ctlplane" bridge.
                          NOTE: If your UnderCloud's network is already configured properly, this could disrupt it, making overcloud API unreachable
                          For more details, see: "VALIDATING THE OVERCLOUD" on https://access.redhat.com/documentation/en/red-hat-openstack-platform/10-beta/paged/director-installation-and-usage/chapter-6-performing-tasks-after-overcloud-creation

            - title: Overcloud storage
              options:
                  storage-external:
                      type: Bool
                      help: Whether to use an external storage rather than setting it up with the director
                      default: no

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
                      help:
                        Specifies a sub-folder under the files/roles/ folder where InfraRed should look for the roles files.
                        InfraRed will use the composable roles appraoch when this flag is defined


            - title: Overcloud compute
              options:
                  compute-ssh:
                      type: Bool
                      default: no
                      help: |
                          Whether to enable SSH communication between compute nodes.
                          This is required when a migration needs to work on a non shared storage scenarios.

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
                          Perform minor update of overcloud to the 'build' specified. Default: 'None'
                          It can be used with --upgrade, when you want to upgrade to specific 'build'
                          NOTE: Currently, minor update is supported with IR just for verions 10 and 11.
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

            - title: Ironic Configuration
              options:
                  vbmc-username:
                      type: Value
                      default: admin
                      help: |
                        VBMC username (Relevant when Ironic's driver is 'pxe_ipmitool' - OSP >= 11)
                  vbmc-password:
                      type: Value
                      default: password
                      help: |
                        VBMC password (Relevant when Ironic's driver is 'pxe_ipmitool' - OSP >= 11)
