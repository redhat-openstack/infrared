---
command:
    subcommands:
        - name: packstack
          help: OpenStack installation using Packstack
          include_groups: ['Logging arguments', 'Inventory arguments', 'Common arguments', 'Configuration file arguments']
          groups:
                - name: Firewall
                  options:
                      - name: firewall
                        type: YamlFile
                        help: The firewall configuration
                        default: default.yml

                - name: Storage
                  options:
                       - name: storage
                         complex_type: YamlFile
                         help: Storage
                       - name: storage-backend
                         complex_type: YamlFile
                         help: Storage backend

                - name: Config
                  options:
                       - name: config
                         complex_type: YamlFile
                         help: Packstack Configuration
                         default: default.yml

                - name: Debug
                  options:
                       - name: osdebug
                         help: Install OS with DEBUG
                         default: y
                         choices: ["y", "n"]


                - name: Messaging
                  options:
                       - name: messaging-variant
                         help: Messaging type
                         default: rabbitmq
                         choices: ["rabbitmq", "qpid"]

                - name: Network
                  options:
                       - name: network
                         complex_type: YamlFile
                         help: Network
                         default: neutron.yml
                       - name: network-variant
                         complex_type: YamlFile
                         help: Network variant
                         default: neutron_ml2-vxlan.yml

                - name: Product
                  options:
                       - name: product-version
                         help: The product version
                         required: yes
                         choices: ["7", "8", "9"]
                       - name: product-build
                         help: The product build
                         default: latest

                - name: Cleanup
                  options:
                      - name: cleanup
                        action: store_true
                        help: Clean given system instead of running playbooks on a new one.
                        nested: no
                        silent:
                            - "product-version"
