---
subparsers:
    ospd:
        formatter_class: RawTextHelpFormatter
        help: Installs openstack using OSP Director
        groups:
            - title: Product
              options:
                product-version:
                    type: Value
                    help: The product version
                    required: yes
                    choices: ["7", "8", "9"]
                product-build:
                    type: Value
                    help: The product build
                    default: latest
                product-core-version:
                    type: Value
                    help: The product core version
                    required: yes
                    choices: ["7", "8", "9"]
                product-core-build:
                    type: Value
                    help: The product core build
                    default: latest

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
                overcloud-hostname:
                    type: Value
                    help: Specifies whether we should use custom hostnames for controllers
                    default: 'no'

            - title: Overcloud storage
              options:
                storage:
                    type: YamlFile
                    help: The overcloud storage type
                    default: no-storage.yml

            - title: Product images
              options:
                images-task:
                    type: Value
                    help: |
                        Specifies the source for the OverCloud images:
                        * RPM - packaged with product (versions 8 and above)
                        * IMPORT - fetch from external source (versions 7 and 8). Requires to specify '--image-url'.
                        * BUILD - build images locally (takes longer)
                    choices: [import, build, rpm]
                    default: rpm
                images-url:
                    type: Value
                    help: Specifies the import image url. Required only when images task is 'import'

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

            - title: Loadbalancer
              options:
                loadbalancer:
                    type: YamlFile
                    help: The loadbalancer to use

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
