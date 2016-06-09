---
subparsers:
    packstack:
        help: OpenStack installation using Packstack
        groups:
            - title: Firewall
              options:
                firewall:
                    type: YamlFile
                    help: The firewall configuration
                    default: default.yml

            - title: Storage
              options:
                  storage:
                      type: YamlFile
                      help: Storage
                  storage-backend:
                      type: YamlFile
                      help: Storage backend

            - title: Config
              options:
                  config:
                      type: YamlFile
                      help: Packstack Configuration
                      default: default.yml

            - title: Debug
              options:
                  osdebug:
                      type: Value
                      help: Install OS with DEBUG
                      default: y
                      choices: ["y", "n"]


            - title: Messaging
              options:
                  messaging-variant:
                      type: Value
                      help: Messaging type
                      default: rabbitmq
                      choices: ["rabbitmq", "qpid"]

            - title: Network
              options:
                  network:
                      type: YamlFile
                      help: Network
                      default: neutron.yml
                  network-variant:
                      type: YamlFile
                      help: Network variant
                      default: neutron_ml2-vxlan.yml

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
