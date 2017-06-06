plugin_type: install
subparsers:
    tripleo-undercloud:
        description: Install TripleO on a designated undercloud node
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Quickstart Menu
              options:
                  quickstart-backup:
                      type: Bool
                      help: |
                          This will create an undercloud snapshot for use with the `--quickstart-restore` flag
                  quickstart-restore:
                      type: Bool
                      help: |
                          This will restore an undercloud from a pre-made snapshot created by the `--quickstart-backup` flag
                  quickstart-filename:
                      type: Value
                      help: |
                          When used with `quickstart-backup`, it will create this file
                          When used with `quickstart-restore`, it will use this file as source
                      default: "undercloud-quickstart.qcow2"

            - title: Undercloud Configuration
              options:
                  config-file:
                      type: FileValue
                      help: |
                          Path to a custom undercloud.conf file to use for deployment.
                          If not set, it will look under `templates` path for a file named `undercloud.conf`.
                          If no `undercloud.conf` file found, it will use default `/usr/share/instack-undercloud/undercloud.conf.sample`
                          that is provided by the installation.

                  config-options:
                      type: IniType
                      action: append
                      help: |
                          Forces additional Undercloud configuration (undercloud.conf) options.
                          Format: --config-options section.option:value1 --config-options section.option:value

                  ssl:
                      type: Bool
                      help: |
                          Specifies whether ths SSL should be used for undercloud
                          A self-signed SSL cert will be generated.
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
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                        - pike

                  build:
                      help: |
                          String represents a timestamp of the OSP puddle
                          (for the given product core version).
                          Supports any rhos-release labels.
                          Examples: "passed_phase1", "2016-08-11.1", "Y1", "Z3", "GA"
                      type: Value
                      default: latest

                  director-build:
                      help: |
                          String represents a timestamp of the OSPd puddle
                          (for the given product core version).
                          Supports any rhos-release labels.
                          Examples: "passed_phase1", "2016-08-11.1", "Y1", "Z3", "GA"
                          Only applies for versions 7-9
                          If missing, will match "build".
                      type: Value

                  buildmods:
                      type: Value
                      help: |
                          List of flags for rhos-release module.
                          Currently works with
                          pin - pin puddle (dereference 'latest' links to prevent content from changing)
                          flea - enable flea repos
                          unstable - this will enable brew repos or poodles (in old releases)
                          none - use none of those flags
                      default: pin

            - title: TripleO User
              options:
                  user-name:
                      type: Value
                      help: The installation user name. Will be generated if missing
                      default: stack

                  user-password:
                      type: Value
                      help: The installation user password
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
                  repos-urls:
                      type: Value
                      help: |
                          comma separated list of URLs to download repo files to ``/etc/yum.repos.d``

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
                          Images source for 'import' and 'build' tasks.
                          For 'import' - points to pre-build overcloud images. Required.
                          For 'build' - points to an image that will be used as the base for building the overcloud, instead of the default cloud guest image.
                      required_when: "images-task == import"

                  images-update:
                      type: Bool
                      help: |
                          Update OverCloud image with repo details.
                      default: no

                  images-packages:
                      type: Value
                      help: |
                          List of packages to install seperated by commas.
                          Requires ``--images-repos=yes``
                          Example: vim,git

                  images-cleanup:
                      type: Bool
                      help: |
                          Removes all the downloaded images when images-task is in 'rpm' or 'import'
                      default: yes

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
