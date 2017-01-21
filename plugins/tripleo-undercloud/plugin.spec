plugin_type: install
description: Install Tripleo on a designated undercloud node
subparsers:
    tripleo-undercloud:
        # FIXME(yfried): duplicates "description"
        help: Install Tripleo on a designated undercloud node
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
                      type: Value
                      help: |
                          Path to a custom undercloud.conf file to use for deployment.
                          If not set, it will look under `templates` path for a file named `undercloud.conf`.
                          If no `undercloud.conf` file found, it will use default `/usr/share/instack-undercloud/undercloud.conf.sample`
                          that is provided by the installation.

                  config-options:
                      type: KeyValueList
                      help: |
                          Forces additional Undercloud configuration (undercloud.conf) options.
                          Format: --config-options="section.option:value1,section.option:value".

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
                      default: ''

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
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata

                  build:
                      help: |
                          "String represents a timestamp of the OSP puddle
                          (for the given product core version).
                          Examples: 'latest', '2016-08-11.1'"
                      type: Value
                      default: latest

            - title: Tripleo User
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
                  repos-config:
                      type: Value
                      help: |
                          YAML file
                          define new repositories or update exsiting according to file.
                          see documentaion for more details
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
                          * RPM - packaged with product (versions 8 and above)
                          * IMPORT - fetch from external source (versions 7 and 8). Requires to specify '--image-url'.
                          * BUILD - build images locally (takes longer)
                      choices:
                          - rpm
                          - import
                          - build

                  images-url:
                      type: Value
                      help: |
                          Specifies the import image url.
                          Required when images task is 'import'
                          When images task is 'build', this is an optional source for base_image to start from.
                      required_when: "images-task == import"

                  images-repos:
                      type: Bool
                      help: |
                          Update OverCloud image with repo details.
                      default: yes

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
