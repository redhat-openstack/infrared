---
config:
    plugin_type: install
subparsers:
    tripleo-undercloud:
        description: Install TripleO on a designated undercloud node
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
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
                  dest-path:
                      type: Value
                      help: |
                          Path on destination server where the UC backup image will be stored
                  dest-key:
                      type: FileValue
                      help: |
                          Key file to send to the remote server in order to transfer the UC backup image
                  dest-user:
                      type: Value
                      help: |
                          Username for destination server (in case key was not provided)
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

            - title: Undercloud Configuration
              options:
                  config-file:
                      type: FileValue
                      help: |
                          Path to a custom undercloud.conf file to use for deployment.
                          If not set, it will look under `templates` path for a file named `undercloud.conf`.
                          If no `undercloud.conf` file found, it will use default `/usr/share/instack-undercloud/undercloud.conf.sample`
                          that is provided by the installation.

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
                      default: clock.redhat.com

                  overcloud-domain:
                      type: Value
                      help: |
                          DNS domain name to use when deploying the overcloud. The overcloud
                          parameter "CloudDomain" must be set to a matching value.
                      default: ''

                  deploy_interface_default:
                      type: Value
                      default: iscsi
                      help: |
                          This option (when set to direct) changes the default in Ironic for the value
                          of deploy_interface from iscsi to direct.
                      choices:
                          - iscsi
                          - direct

            - title: Splitstack deployment
              options:
                  splitstack:
                      type: Bool
                      default: no
                      help: |
                        Whether to use splistack deployment

                  tls-everywhere:
                      type: Bool
                      help: |
                          Specifies whether TLS Everywhere with FreeIPA should be implemented
                      default: no

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
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                        - pike
                        - queens
                        - rocky
                        - stein
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
                      type: Value
                      help: |
                          comma separated list of URLs to download repo files to ``/etc/yum.repos.d``
                  repos-skip-release:
                      type: Bool
                      help: |
                          specifies whether the rhos/rdo-release tools should
                          be used to install tripleo packages. This flag also disables installation of the extra cdn
                          repositories.
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
                      default: "docker-registry.engineering.redhat.com"

                  registry-namespace:
                      type: Value
                      help: The alternative docker registry namespace to use for undercloud deployment.
                      default: "rhosp14"

                  registry-skip-puddle:
                      type: Bool
                      help: |
                          Skip reading any private puddle files to auto-detect the containers parameters
                      default: False

                  registry-tag:
                      type: Value
                      help: The images tag

                  registry-tag-discover:
                      type: Value
                      help: |
                          If this option is set then infrared will try to auto discover tag
                      default: False

                  registry-undercloud-skip:
                      type: Bool
                      help: Avoid using and mass populating the undercloud registry.
                            The registry or the registry-mirror will be used directly when possible,
                            recommended to use this option when you have very good bandwidth to your registry.
                      default: False

                  registry-prefix:
                      type: Value
                      help: |
                          Container images prefix
                      default: 'openstack-'
