---
subparsers:
    packstack:
        help: OpenStack installation using Packstack
        include_groups: ['Ansible options', 'Inventory hosts options', 'Common options', 'Configuration file options']
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
                      choices: ["7", "8", "9", "10"]
                  product-build:
                      type: Value
                      help: The product build
                      default: latest

            - title: Cleanup
              options:
                  cleanup:
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      silent:
                        - "product-version"
