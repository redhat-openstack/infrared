---
config:
    plugin_type: install
subparsers:
    tripleo-undercloud:
        description: Install TripleO on a designated undercloud node
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

            - title: Snapshot Menu
              options:
                  snapshot-backup:
                      type: Bool
                      help: |
                          This will create an undercloud snapshot for use with the `--snapshot-restore` flag
                  dest-address:
                      type: Value
                      help: |
                          This will be the remote server where the UC backup image will be stored
                  dest-mirror-address:
                      type: Value
                      help: |
                          This will be the mirror site where the UC backup image will be stored
                  dest-path:
                      type: Value
                      help: |
                          Path on destination server where the UC backup image will be stored
                  dest-mirror-path:
                      type: Value
                      help: |
                          Path on destination mirror server where the UC backup image will be stored
                  dest-key:
                      type: FileValue
                      help: |
                          Key file to send to the remote server in order to transfer the UC backup image
                  dest-user:
                      type: Value
                      help: |
                          Username for destination server (in case key was not provided)
                  hieradata-config:
                      type: Dict
                      help: |
                          Optional configuration to set via hieradata
                          Use  --hieradata-config this::key=value,that::key=another_value
                  snapshot-restore:
                      type: Bool
                      help: |
                          This will restore an undercloud from a pre-made snapshot created by the `--snapshot-backup` flag
                          Use --snapshot-image to specify image to use for restore.
                  snapshot-image:
                       type: Value
                       help: |
                          The url or path to the image to restore the undercloud from.
                  snapshot-filename:
                      type: Value
                      help: |
                          When used with `snapshot-backup`, it will create this file
                          When used with `snapshot-restore`, it will use this file as the disk name for the domain
                      default: "undercloud-snapshot.qcow2"
                  snapshot-access-network:
                      type: Value
                      help: |
                           Will determin the access network to reach the undercloud after snapshot restore
                      default: "external"

            - title: Undercloud Configuration
              options:
                  config-file:
                      type: FileValue
                      help: |
                          Path to a custom undercloud.conf (jinja template) file to use for deployment.
                          If value set to `none` it will use the `/usr/share/instack-undercloud/undercloud.conf.sample`
                          from the undercloud node.

                  boot-mode:
                      type: Value
                      help: |
                          The default boot mode is the legacy BIOS mode.
                          Newer systems might require UEFI boot mode instead of the legacy BIOS mode.
                      choices:
                          - bios
                          - uefi
                      default: bios

                  config-options:
                      type: IniType
                      action: append
                      help: |
                          Forces additional Undercloud configuration (undercloud.conf) options.
                          Format: --config-options section.option=value1 --config-options section.option=value

                  ssl:
                      type: Bool
                      help: |
                          Specifies whether ths SSL should be used for undercloud
                          A self-signed SSL cert will be generated.
                          Starting with OSP 14 ssl is enabled by default regardless of this option.
                      default: no

                  tls-ca:
                      type: Value
                      help: |
                          Specifies the remote URL to fetch a specific CA from.
                          Example:
                                --tls-ca=https://foo.com/ca.pem
                      default: ''

                  undercloud-extra-args:
                      type: Value
                      help: |
                          Extra arguments to be passed to the openstack undercloud deploy script
                          Example:
                                --undercloud-extra-args="--use-heat"
                      default: ''

                  shade-host:
                      type: Value
                      help: |
                          The name of the host which will be used as a shade node to handle all the os_* ansible
                          modules requests. If this value is not provided, Infrared will use hypervisor host if present,
                          otherwise undercloud is used.
                          Example:
                                --shade-host undercloud-0

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


                  overcloud-domain:
                      type: Value
                      help: |
                          DNS domain name to use when deploying the overcloud. The overcloud
                          parameter "CloudDomain" must be set to a matching value.
                      default: 'redhat.local'

                  freeipa-domain:
                      type: Value
                      help: |
                          Set the FreeIPA domain parameter.
                      default: 'redhat.local'

                  deploy_interface_default:
                      type: Value
                      default: iscsi
                      help: |
                          This option (when set to direct) changes the default in Ironic for the value
                          of deploy_interface from iscsi to direct.
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

                  reboot-timeout:
                      type: Value
                      default: 1200
                      help: |
                          The timeout for the undercloud host to come back from a reboot after package updates or
                          an upgrade.

            - title: Splitstack deployment
              options:
                  splitstack:
                      type: Bool
                      default: no
                      help: |
                        Whether to use splistack deployment

                  ipa-forwarder:
                      type: Value
                      help: |
                          Specifies the DNS forwarder of BIND on the IPA server
                      default: 'hypervisor'

                  freeipa-undercloud-interface:
                      type: Value
                      help: |
                          Undercloud external network interface
                      default: 'eth2'

                  tls-everywhere:
                      type: Bool
                      help: |
                          Specifies whether TLS Everywhere with FreeIPA should be implemented
                      default: no

                  enable-novajoin:
                      type: Bool
                      help: |
                          Specifies whether TLS Everywhere with FreeIPA will use novajoin on the undercloud
                      default: yes

            - title: Setup Undercloud Packages
              options:
                  mirror:
                      type: Value
                      help: |
                          Enable usage of specified mirror (for rpm, pip etc) [brq,qeos,tlv - or hostname].
                          (Specified mirror needs to proxy multiple rpm source hosts and pypi packages.)

                  version:
                      type: Value
                      help: |
                          The product version (product == director)
                          Numbers are for OSP releases
                          Names are for RDO releases
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
                  build:
                      help: |
                          String represents a timestamp of the OSP puddle.
                          Note: for versions 6 < OSPd < 10 to specify director
                          version use '--director-build' flag.
                          (for the given product core version).
                          Supports any rhos-release labels.
                          RDO supported labels: master-tripleo-ci
                          Examples: "passed_phase1", "2016-08-11.1", "Y1", "Z3", "GA"
                      type: Value

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

                  from-source:
                      type: NestedList
                      action: append
                      help: |
                          Install tripleo components from upstream git repository
                          --from-source name=openstack/neutron,refs=refs/changes/REF_ID
                          --from-source name=openstack/python-tripleoclient

                  enable-testing-repos:
                      type: Value
                      help: |
                          Let you the option to enable testing/pending repos with rhos-release. Multiple values have to be coma separated.
                          Examples: --enable-testing-repos rhel,extras,ceph or --enable-testing-repos all

                  ceph-repos:
                      type: Bool
                      default: yes
                      help: Skips the ceph repository configuration in he Undercloud during rhos-release execution if set to false.

                  validate:
                      type: Bool
                      default: yes
                      help: Specifies whether we should run pre validation tasks

                  post:
                      type: Bool
                      help: Specifies whether we should run post install tasks
                      default: yes

                  workarounds:
                      type: Value
                      help: |
                          Specifies the external workarounds file location.
                          Example:  --workarounds 'http://server.localdomain/workarounds.yml'
                      default: ''

                  packages:
                      type: Value
                      help: |
                          Comma,separated list of packages to install on undercloud before Undercloud install.
                          Example: vim,git,http://<some_url>/openvswitch-selinux-extra-policy-1.0-15.el8fdp.noarch.rpm

            - title: TripleO User
              options:
                  user-name:
                      type: Value
                      help: The installation user name. Will be generated if missing
                      default: stack

                  user-password:
                      type: Value
                      help: The installation user password. Change it for public deployments.
                      default: stack

            - title: Custom Repositories
              options:
                  cdn:
                      type: FileValue
                      help: |
                          YAML file
                          Register the undercloud with a Red Hat Subscription Management platform.
                          see documentation for more details
                  satellite-clean-nodes:
                      type: Bool
                      default: False
                      help: |
                          Unregister undercloud and overcloud nodes from satellite server
                  repos-config:
                      type: VarFile
                      help: |
                          YAML file
                          define new repositories or update existing according to file.
                          see documentation for more details
                  upload-extra-repos:
                      type: Bool
                      default: False
                      help: |
                          Specifies if custom undercloud repos generated by repos-config should be uploaded to overcloud image
                  repos-urls:
                      type: ListValue
                      help: |
                          Comma,separated list of URLs of YUM/DNF repo files to download to ``/etc/yum.repos.d``
                  repos-skip-release:
                      type: Bool
                      help: |
                          specifies whether the rhos/rdo-release tools should
                          be used to install tripleo packages. This flag also disables installation of the extra cdn
                          repositories.
                  custom-sources-script-url:
                      help: |
                          Script which is downloaded and executed at repo and registry setup time,
                          IR provides context for the scripts via environment variables.
                          Implies repos-skip-release , the script can call foo-release if wishes
                          In case of a remote url you can pass get parameters.
                      default: ""
                  custom-sources-script-args:
                      help: |
                           Extra arguments for the custom-sources script.
                  skip-remove-repo:
                      type: Value
                      action: append
                      help: |
                          In the rhos-release role all repositories are clean up before tripleo-undercloud
                          deployment, if some repos are required during deployment then use option
                          '--skip-remove-repo' and specify path to the repository file. In that case this
                          repository will be ignored during delete procedure.
                          Example: --skip-remove-repo /etc/yum.repos.d/rhel-updates.repo

            - title: Overcloud images
              options:
                  images-task:
                      type: Value
                      help: |
                          Specifies the source for the OverCloud images:
                          * rpm - packaged with product (versions 8 and above)
                          * import - Download pre-built images from a given source (versions 7 and 8). Requires '--images-url'.
                          * build - build images locally (takes longer) on top of regular cloud guest image. CentOS/RHEL will be used for RDO/OSP.
                      choices:
                          - rpm
                          - import
                          - build

                  images-url:
                      type: Value
                      help: |
                          Images source for 'import' and 'build' tasks, and RPM source for 'rpm' task
                          For 'import' - points to pre-build overcloud images. Required.
                          For 'build' - points to an image that will be used as the base for building the overcloud, instead of the default cloud guest image.
                          For 'rpm' - points to RPM that will be used. If RPM has dependencies, you have to provide them also. Locations have to be separated with comma.
                      required_when: "images-task == import"

                  images-update:
                      type: Bool
                      help: |
                          Update OverCloud image with repo details.
                      default: no

                  images-packages:
                      type: Value
                      help: |
                          List of packages to install separated by commas.
                          Example: vim,git

                  images-remove-packages:
                      type: Value
                      help: |
                          List of packages to uninstall separated by commas.
                          Example: vim,git

                  images-remove-no-deps-packages:
                      type: Value
                      help: |
                          List of packages to force remove using 'rpm -e --nodeps', separated by commas.
                          Example: openvswitch,python-openvswitch
                      ansible_variable: images_remove_no_deps_packages

                  images-cleanup:
                      type: Bool
                      help: |
                          Removes all the downloaded images when images-task is in 'rpm' or 'import'
                      default: yes

                  disk-pool:
                      type: Value
                      help: |
                        A path to the undercloud image. Default is Storage Pool from libvirt
                      default: "/var/lib/libvirt/images"

                  overcloud-update-kernel:
                      type: Bool
                      help: |
                          Updating default overcloud kernel with kernel files retrieved from customized overcloud image
                      default: no

                  overcloud-image-name:
                      type: value
                      choices:
                        - full
                        - hardened-uefi-full
                      help: |
                          Specifies the overcloud image name:
                          * full - overcloud-full.qcow2
                          * hardened-uefi-full - overcloud-hardened-uefi-full.qcow2

                  download-ppc64le-images:
                      type: Bool
                      help: |
                          Enables download of ppc64le cloud images and their upload into glance for multiarch deployments
                      default: false

            - title: Undercloud Upgrade
              options:
                  upgrade:
                      type: Bool
                      help: |
                          Undercloud Upgrade.
                          Note: Currently, there is upgrade possibility from version 9 to version 10 only.

            - title: Undercloud Update
              options:
                  update-undercloud:
                      type: Bool
                      help: |
                          Undercloud Update.
                          Note: Infrared support update for RHOSP version 11 only.
                  osrelease:
                      type: Value
                      help: |
                          Override the default RHEL version. Default 'ansible_distribution_version'

            - title: Containers
              options:
                  registry-mirror:
                      type: Value
                      help: The alternative docker registry to use for undercloud deployment.
                            Defaults to value per-compose/puddle.

                  registry-namespace:
                      type: Value
                      help: The alternative docker registry namespace to use for undercloud deployment.
                            Defaults to value per compose/puddle (in other case to "rhosp${version}" e.g. rhosp14)

                  registry-skip-puddle:
                      type: Bool
                      help: |
                          Skip reading any private puddle files to auto-detect the containers parameters
                      default: False

                  registry-tag:
                      type: Value
                      help: The images tag

                  registry-undercloud-skip:
                      type: Bool
                      help: Avoid using and mass populating the undercloud registry.
                            The registry or the registry-mirror will be used directly when possible,
                            recommended to use this option when you have very good bandwidth to your registry.
                      default: False

                  registry-prefix:
                      type: Value
                      help: |
                          Container images prefix.
                          Defaults to value per compose/puddle (otherwise to 'openstack-').

                  bip-address:
                      type: Value
                      help: |
                          The subnet for the undercloud docker interface
                          on the undercloud

                  registry-ceph-namespace:
                      type: Value
                      help: namespace for the ceph container

                  registry-ceph-image:
                      type: Value
                      help: image for the ceph container

                  registry-ceph-tag:
                      type: Value
                      help: tag used with the ceph container

                  registry-ceph-username:
                      type: Value
                      help: An username/token-paired username string to authenticate with a ceph registry

                  registry-ceph-password:
                      type: Value
                      help: A password/token string to authenticate with a ceph registry

                  registry-custom-script-url:
                      type: Value
                      help: Use the custom script to configure registries and container sources
                      default: ''

                  registry-custom-script-args:
                      type: Value
                      help: Arguments passed to the registry-custom-script.
                      default: ''

                  registry-insecure-containers-parameter:
                      type: Value
                      help: |
                          Designate an insecure registry using the DockerInsecureRegistryAddress flag
                          inside the containers-prepare-parameter file
            - title: Others
              options:
                  selinux:
                      type: Value
                      help: Change the selinux state.
                      choices: ["enforcing", "permissive", "disabled"]
                      default: "enforcing"
