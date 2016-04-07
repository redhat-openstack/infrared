---
subparsers:
    ospd:
        help: Installs openstack using OSP Director
        groups:
            - title: Firewall
              options:
                firewall:
                    type: YamlFile
                    help: The firewall configuration
                    default: default.yml

            - title: Product
              options:
                product:
                    type: YamlFile
                    help: The product to install
                    required: yes
                product-version:
                    type: YamlFile
                    help: The product version
                    required: yes

            - title: Undercloud
              options:
                undercloud-config:
                    type: YamlFile
                    help: The undercloud config details
                    default: default.yml

            - title: Overcloud
              options:
                overcloud-ssl:
                    type: Value
                    help: Specifies whether ths SSL should be used for overcloud
                    default: 'no'

            - title: Overcloud storage
              options:
                storage:
                    type: YamlFile
                    help: The overcloud storage type
                    default: ceph.yml

            - title: Overcloud images
              options:
                images-task:
                    type: Value
                    help: Specifies whether the images should be built or imported
                    required: yes
                    #choices: [import, build]
                images-files:
                    type: YamlFile
                    help: The list of images for overcloud nodes
                    required: yes
                images-url:
                    type: Value
                    help: The images download url
                    required: yes

            - title: Overcloud Network
              options:
                network-backend:
                    type: Value
                    help: The overcloud network backend.
                    default: vxlan
                network-protocol:
                    type: Value
                    help: The network protocol for overcloud
                    default: ipv4
                network-isolation:
                    type: YamlFile
                    help: The overcloud network isolation type
                    required: yes
                network-isolation-template:
                    type: YamlFile
                    help: The overcloud network isolation template

            - title: Version
              options:
                version-major:
                    type: Value
                    help: The OSPd major version
                    default: 7
                version-minor:
                    type: Value
                    help: The OSPd minor version
                    default: 3
                build:
                    type: Value
                    help: The OSPd build
                    default: latest

            - title: User
              options:
                user-name:
                    type: Value
                    help: The installation user name
                    default: stack
                user-password:
                    type: Value
                    help: The installation user password
                    default: stack

            - title: Workarounds
              options:
                workarounds:
                    type: YamlFile
                    help: The list of workarounds to use during install

            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook execution stage
                  cleanup:
                      action: store_true
                      help: Clean given system instead of provisioning a new one
                  input:
                      action: append
                      type: str
                      short: i
                      help: Input settings file to be loaded before the merging of user args
                  output:
                      type: str
                      short: o
                      help: 'File to dump the generated settings into (default: stdout)'
                  extra-vars:
                      action: append
                      short: e
                      help: Extra variables to be merged last
                      type: str
                  from-file:
                      type: IniFile
                      help: the ini file with the list of arguments
                  generate-conf-file:
                      type: str
                      help: generate configuration file (ini) containing default values and exits. This file is than can be used with the from-file argument
