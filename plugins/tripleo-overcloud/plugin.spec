---
config:
    plugin_type: install
subparsers:
    tripleo-overcloud:
        description: Install a TripleO overcloud using a designated undercloud node
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Failure handling options
              options:
                  retry-http-codes:
                      type: ListValue
                      help: |
                          Comma,separated list of http codes to retry on. If 'get_url' or (potentially) other http(s) task fails with one of these codes it will be retried (up to 3 times usually).
                      # https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
                      default: 408,460,504,522,524,598
                      ansible_variable: 'retry_http_codes'

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

                  delete:
                      type: Bool
                      help: Deletes existing Overcloud
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

                  container-extra-repos:
                      type: ListValue
                      help: |
                            List of repositories URLs to use in containers to update existing packages.
                            It will link provided repos to the container and perform 'yum update'.

                  update_repo:
                      type: Value
                      help: |
                            To update containers with packages from remote repositories you have to specify
                            the name of the repositry. This option should be used together with container-extra-repos.

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

                  container-images-urls:
                      type: ListValue
                      help: |
                          Comma,separated list of container images URLs. These URLs have to point at images in docker/podman registry.
                          Images from URLs in this container-images-urls option override the default images URLs normally retrieved form puddle/compose.
                          Example:
                              --container-images-urls brew-pulp-docker01.web.prod.ext.phx2.redhat.com:8888/rhosp13/openstack-nova-compute:13.0-92.1564415447,brew-pulp-docker01.web.prod.ext.phx2.redhat.com:8888/rhosp13/openstack-nova-libvirt:13.0-95.1564415448

                      ansible_variable: 'install_container_images_urls'

                  overcloud-image-name:
                      type: Value
                      choices:
                        - full
                        - hardened-uefi-full
                      help: |
                          Specifies the overcloud image name:
                          * full - overcloud-full.qcow2
                          * hardened-uefi-full - overcloud-hardened-uefi-full.qcow2

                  cdn:
                      type: FileValue
                      help: |
                          YAML file
                          Register the undercloud with a Red Hat Subscription Management platform.
                          see documentation for more details

                  registry-mirror:
                      type: Value
                      help: |
                          The alternative docker registry to use for deployment. DEPRECATED.
                          New version of osp handles the registry mirror only at the undercloud step.

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
                      help: The images tag.

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
                      help: namespace for the ceph container

                  registry-ceph-image:
                      type: Value
                      help: image for the ceph container

                  registry-ceph-tag:
                      type: Value
                      help: tag used with the ceph container

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
                        - "15"
                        - "15-trunk"
                        - "16"
                        - "16-trunk"
                        - "17"
                        - "17.0"
                        - "17.1"
                        - "17-trunk"
                        - "16.0"
                        - "16.0-trunk"
                        - "16.1"
                        - "16.1-trunk"
                        - "16.2"
                        - "16.2-trunk"
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                        - pike
                        - queens
                        - rocky
                        - stein
                        - train

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
                      maximum: 240

                  instackenv-file:
                      type: Value
                      help: The path to the instackenv.json configuration file used for introspection.

                  instackenv-useports:
                      type: Bool
                      default: no
                      help: |
                          Use "ports" definition instead of "mac" in instackenv.json file.
                          This option is available since Rocky (also see RHBZ#1909010).

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
                            NOTE: This parameter will be ignored if 'ntp-pool' is given.
                      default: clock1.rdu2.redhat.com

                  ntp-pool:
                      type: Value
                      help: |
                            Hostname or IP address of one or more NTP servers separated by commas.
                            (Supported from OSP15 and newer)
                            NOTE: This parameter takes precedence over 'ntp-server'.

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

                  ppc64le-nodes:
                      type: Bool
                      help: Specifies if ppc64le nodes are being utilized in this overcloud deployment
                      default: false

            - title: Overcloud Options
              options:
                  overcloud-predeploy-action:
                      type: Value
                      help: Specify a custom command to run before the Overcloud deploy script

                  overcloud-postdeploy-action:
                      type: Value
                      help: Specify a custom command to run post Overcloud deploy script

                  overcloud-debug:
                      type: Bool
                      default: yes
                      help: Specifies whether overcloud service should enable debug mode

                  overcloud-tripleoclient-debug:
                      type: Bool
                      default: no
                      help: Specifies whether tripleo client debug mode is enabled during overcloud deploy

                  overcloud-ssl:
                      type: Bool
                      default: no
                      help: Specifies whether ths SSL should be used for overcloud

                  overcloud-use-dns-names:
                      type: Bool
                      default: no
                      help: Specifies whether to use DNS names in the subject DN for the public certs

                  overcloud-host-config-and-reboot:
                      type: Bool
                      default: no
                      help: Specifies if compute parameters require host config and reboot to take effect

                  overcloud-fencing:
                      type: Bool
                      default: no
                      help: Specifies whether fencing should be configured and enabled on the overcloud
                            (Supported from OSP13 and newer)

                  overcloud-fencing_delay:
                      type: Value
                      default: 0
                      help: Specifies the fencing delay that needs to be configured
                            (Makes only sense when overcloud-fencing is true)

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

                          It is also possible to have . (dot) included in key by escaping it.
                          Example:
                              --config-heat "ControllerExtraConfig.opendaylight::log_levels.org\.opendaylight\.netvirt\.elan=TRACE"

                          should inject the following yaml to "overcloud deploy" command:

                               ---
                               parameter_defaults:
                                   ControllerExtraConfig:
                                       opendaylight::log_levels:
                                           org.opendaylight.netvirt.elan: TRACE

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

                  undercloud-packages:
                      type: Value
                      help: |
                          Comma delimited list of names or URLs of the packages to be installed on
                          undercloud before Overcloud deployment, uses "yum" package manager.
                          NOTE: When trying to install packages with this parameter please be sure
                          that the appropriate Yum repositories have been enabled.
                          Examples:
                              --undercloud-packages python-tripleoclient
                              --undercloud-packages http://download-node-02.eng.bos.redhat.com/composes/auto/ceph-3.1-rhel-7/latest-RHCEPH-3-RHEL-7/compose/Tools/x86_64/os/Packages/golang-1.9.4-1.el7.x86_64.rpm
                              --undercloud-packages vim,http://download-node-02.eng.bos.redhat.com/composes/auto/ceph-3.1-rhel-7/latest-RHCEPH-3-RHEL-7/compose/Tools/x86_64/os/Packages/golang-1.9.4-1.el7.x86_64.rpm

                  fetchfiles-undercloud:
                      type: Value
                      action: append
                      help: |
                          Pairs of 'URL,destfile'. File from 'URL' will be downloaded as 'destfile' (overwrite existing file) on Undercloud.
                          'destfile' is an absolute path on Undercloud ending _with_ file name (because sometimes it's required to change file name).
                          NOTE: this option is _not_ recommended for production jobs or environments. If files of an official product are fetched/overwritten,
                          it's advised to mark jobs using this method as 'experimental' and remove using this fetchfiles as soon as required files are in official release.
                          Example (in case one wants to use files from https://review.openstack.org/#/c/585015/2):
                              --fetchfiles-undercloud https://git.openstack.org/cgit/openstack/tripleo-heat-templates/plain/environments/network-isolation-v6.j2.yaml?h=refs/changes/15/585015/2,/usr/share/openstack-tripleo-heat-templates/environments/network-isolation-v6.j2.yaml
                              --fetchfiles-undercloud https://git.openstack.org/cgit/openstack/tripleo-heat-templates/plain/puppet/services/opendaylight-api.yaml?h=refs/changes/15/585015/2,/usr/share/openstack-tripleo-heat-templates/puppet/services/opendaylight-api.yaml

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

                  overcloud-domain:
                      type: Value
                      help: |
                          Set the CloudDomain parameter. The value for CloudDomain must match the value
                          for overcloud_domain_name that was configured in undercloud.conf if set.
                      default: 'redhat.local'

                  freeipa-domain:
                      type: Value
                      help: |
                          Set the FreeIPA domain parameter.
                      default: 'redhat.local'

                  tls-everywhere:
                      type: Bool
                      help: |
                          Specifies whether TLS Everywhere with FreeIPA should be implemented
                      default: no

                  enable-novajoin:
                      type: Bool
                      help: |
                          Specifies whether TLS Everywhere with FreeIPA will use novajoin on the overcloud
                      default: yes

                  ipa-issue-public-certs:
                      type: Bool
                      help: |
                          Specifies whether certs on the public endpoints will be issued by FreeIPA
                      default: yes

                  ipa-forwarder:
                      type: Value
                      help: |
                          Specifies the DNS forwarder of BIND on the IPA server
                      default: 'hypervisor'

                  fetchfiles-overcloud:
                      type: Value
                      action: append
                      help: |
                          Pairs of 'URL,destfile'. File from 'URL' will be downloaded as 'destfile' (overwrite existing file) in overcloud image which is later used to deploy Overcloud.
                          'destfile' is an absolute path in overcloud image ending _with_ file name (because sometimes it's required to change file name).
                          NOTE: this option is _not_ recommended for production jobs or environments. If files of an official product are fetched/overwritten,
                          it's advised to mark jobs using this method as 'experimental' and remove using this fetchfiles as soon as required files are in official release.
                          Example (in case one wants to use files from https://review.openstack.org/#/c/585015/2):
                              --fetchfiles-overcloud https://git.openstack.org/cgit/openstack/tripleo-heat-templates/plain/environments/network-isolation-v6.j2.yaml?h=refs/changes/15/585015/2,/usr/share/openstack-tripleo-heat-templates/environments/network-isolation-v6.j2.yaml
                              --fetchfiles-overcloud https://git.openstack.org/cgit/openstack/tripleo-heat-templates/plain/puppet/services/opendaylight-api.yaml?h=refs/changes/15/585015/2,/usr/share/openstack-tripleo-heat-templates/puppet/services/opendaylight-api.yaml

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
                          - ipv6-all

                  network-render-templates:
                      type: Bool
                      default: no
                      help: Define configuration with network_data.yaml instead of network-environment.yaml

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

                  network-force-compute-dvr:
                      type: Bool
                      default: no
                      help: On non-DVR setup use compute node with access to the external network.

                  network-override-dvr-nic:
                      type: FileValue
                      help: |
                          Option to provide custom nic template for DVR compute nodes.
                          Example:
                          --network-dvr-nic-override /home/stack/templates/network/nic-configs/compute-dvr.yaml

                  network-l2gw:
                      type: Bool
                      default: no
                      help: Activate APIs and implementations to support L2 Gateways in Neutron

                  network-lbaas:
                      type: Bool
                      default: no
                      help: Deploy Overcloud with LBaaS v2. (OSP >= 13, RDO >= Queens)

                  network-ovn:
                      type: Bool
                      default: no
                      help: Use OVN (HA) instead of ML2 and OVS.

                  network-ovs:
                      type: Bool
                      default: no
                      help: Use ML2/OVS instead of OVN which is the default for RDO Stein / OSP 15.

                  network-data-file:
                      type: Value
                      short: n
                      help: |
                          TripleO offers a default network topology when deploying with network isolation enabled,
                          and this is reflected in the network_data.yaml file in tripleo-heat-templates.
                          This parameter will override the default network_data.yaml to provide different type of network topology.
                          Default Heat templates base directory is /usr/share/openstack-tripleo-heat-templates.
                          Value example:
                          --network-data-file /home/stack/virt/network_data_spine_leaf.yaml
                          Can be used with new templates base directory:
                          --heat-templates-basedir /path/to/openstack-tripleo-heat-templates

                  custom-data-roles-file:
                      type: Value
                      short: r
                      help: |
                          Option to provide custom role data file.
                          Create a roles data yaml file that contains the custom role in addition to the other roles that will be deployed.

                  custom_network_names:
                      type: Value
                      help: |
                          Option to provide custom names for the networks.
                          Note: Custom network names can be provided as values.
                          Value example:
                          --custom_network_name storage=MyStorageNet,storage_mgmt=MyStorageMgmtNet,internal_api=MyInternalApiNet,tenant=MyTenantNet,external=MyExternalNet

                  cleaning-network:
                      type: Bool
                      default: no
                      help: Adds a network for cleaning in OC. Asssumes Ironic in OC was enabled.

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
                          - nfs
                      help: |
                        The storage that we would like to use.
                        If not supplied, Infrared will try to discover storage nodes and select appropriate backed.
                        The 'lvm' value will be used when storage nodes were not found.
                        NOTE: when not using external storage, this will set the default for "--storage-nodes" to 1.

                  ceph-cluster-name:
                      type: Value
                      default: ceph
                      help: |
                        The variable used to change the ceph cluster name, this feature is supported from RHOSP 15. Default value is 'ceph'.

                  ceph-pgnum:
                      type: Value
                      default: 32
                      help: set the default amount of placement groups for the pools in the internal Ceph cluster

                  ceph-initial-conf-file:
                      type: Value
                      default: ''
                      help: |
                          The absolute path of an initial Ceph configuration file. It
                          will be copied to undercloud:/home/stack/initial-ceph.conf
                          and passed to 'openstack overcloud ceph deploy --config'.
                          The inital-ceph.conf supports jinja2 templating and could
                          include {{ ansible_vars }} which are set during infrared
                          run. Only supported for OSP 17 and newer.

                  glance-backend:
                      type: Value
                      choices:
                          - rbd
                          - swift
                          - cinder
                      default: rbd
                      help: |
                        The storage backend type used for glance, enabling to set Swift, RadosGW or Cinder as the backend when deploying internal Ceph. Default value is 'rbd'
                  storage-protocol-backend:
                      type: Value
                      default: NA
                      choices:
                          - nfs-ganesha
                          - nfs
                          - iscsi
                          - NA
                      help: |
                        The storage protocol that we would like to use.
                        nfs-ganesha works only if the storage backand is ceph
                        NOTE: nfs and iscsi are not implemented but added to be decoupled from storage backend parameter
                  nova-nfs-backend:
                      type: Bool
                      help: |
                          This options allows configuring NFS backend for Nova component and includes the appropriate
                          THT template. storage-nova-nfs-share needs to be set when this is set to 'True'
                      default: False

                  storage-nova-nfs-share:
                      type: Value
                      help: |
                        The absolute path to an external NFS storage mount
                        NOTE: this needs to be set when nova-nfs-backend is set to 'True'

                  local-nfs-server:
                      type: Bool
                      help: |
                          Installs a local NFS server on undercloud
                      default: False

                  storage-config:
                      type: Value
                      help: |
                          Storage configuration file (YAML file)
                          __LISTYAMLS__
                      default: internal

                  ceph-osd-type:
                      type: Value
                      help: |
                          From RHCS v3.2 and later 'bluestore' and 'filestore' is available as OSD types.
                      default: bluestore
                      choices:
                          - bluestore
                          - filestore

                  ceph-osd-scenario:
                      type: Value
                      help: |
                          Sets the location of the journal data (for filestore) or the write-ahead log and key-value data (bluestore).
                      default: lvm
                      choices:
                          - lvm
                          - non-collocated
                          - collocated

                  ceph-hci-memreserve:
                      type: Bool
                      help: |
                          For hyperconverged environments, reserve ram per OSD When this is set to true,
                          the is_hci flag is introduced into internal.yaml.
                      default: false

                  ceph-rgw-swift-compatibility:
                      type: Bool
                      help: |
                          Rados Gateway does not respond with same headers as swift.
                          Rados Gateway doesn't enable versioning by default.
                          Changing this to true will add a config flag that forces the responces to match swift's and
                          enable versioning.
                          This is useful when tempest object_storage tests fail due to differences with swift.
                      default: false

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
                  reboot-timeout:
                      type: Value
                      default: 1200
                      help: |
                          The timeout for the undercloud host to come back from a reboot after package updates or
                          an upgrade.
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
                      default: undercloud
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
                          node's resource_class field (available starting with Bare Metal API version 1.21)
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
                  root-disk-override:
                      type: NestedList
                      action: append
                      help: |
                          This option allows to define custom root disk for multi-disk nodes
                          The 'node' field supports 'controller' or 'controller-0' patterns.
                          The 'hint' is property's name that helps to identify the root disk, e.g: serial, wwn
                          The 'hintvalue' is a specific value for a hint's property, e.g: 123-asb-s1be
                          Example:
                              --root-disk-override node=controller,hint=size,hintvalue=50
                              --root-disk-override node=compute-0,hint=name,hintvalue=/dev/sda
                              --root-disk-override node=ceph,hint=rotational,hintvalue=false

                          If this parameter is not set, Infrared will set only ceph root_device to /dev/vda.
                          To override that behavior use -e ceph_default_disk_name=/dev/sdb option.

                  boot-mode:
                      type: Value
                      help: |
                          TripleO supports booting overcloud nodes in UEFI mode instead of the default BIOS mode.
                          This is required to use advanced features like secure boot, and some hardware may only
                          feature UEFI support.
                      default: bios
                      choices:
                          - bios
                          - uefi

                  ironic:
                      type: Bool
                      help: |
                          This options allows adding ironic templates to support overcloud deployment with ironic
                          enabled services. This is required for booting BM instances in overcloud.
                      default: False

                  ironic_inspector:
                      type: Bool
                      help: |
                          This options allows adding ironic-inspector templates to support introspection in overcloud.
                          Note that this option implicitly enables the ironic option.
                      default: False

                  image_direct_deploy:
                      type: Value
                      help: |
                          This option (when set to direct) sets the direct deploy flag on nodes in ironic, instead of the default
                          iscsi method.
                      default: iscsi
                      choices:
                          - iscsi
                          - direct

                  image-download-source:
                      type: Value
                      default: swift
                      help: |
                          This option when using in conjunction with (deploy_interface_default: direct) changes
                          the default in Ironic for the value of image_download_source from swift to http.
                          (swift) IPA ramdisk retrieves instance image from the Object Storage service.
                          (http) IPA ramdisk retrieves instance image from HTTP service served at conductor nodes.
                          Example:
                                --image-download-source http
                      choices:
                          - swift
                          - http
                  remove-br-baremetal:
                      type: Bool
                      help: |
                          When set to true, ironic will not use the br-baremetal network for introspection but only
                          br-ex. This is useful in environments with less than 3 nics (where vlans are used for
                          network separation).
                      default: False

            - title: ansible facts
              options:
                  collect-ansible-facts:
                      type: Bool
                      help: Save ansible facts as json file(s)
                      default: False
