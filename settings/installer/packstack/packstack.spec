---
subparsers:
    packstack:
        help: OpenStack installation using Packstack
        include_groups: ['Ansible options', 'Inventory hosts options', 'Common options', 'Configuration file options']
        groups:
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
                  public-network:
                      type: Value
                      help: Deploy "public" external network on the Cloud as post-install.
                      choices: ['yes', 'no']
                      default: 'yes'
                  public-subnet:
                      type: YamlFile
                      help: |
                          Subnet detail for "public" external network on the OverCloud as post-install.
                          CIDR
                          Allocation Pool
                          Gateway

                          If empty, will try to discover using "neutron.subnets.external" details
                  # TODO(yfried): decouple this from openstack provisioner.

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

            - title: Extra components
              options:
                  component-sahara:
                      type: Value
                      help: Sahara enabled
                      default: 'n'
                      choices: ['y', 'n']
                  component-trove:
                      type: Value
                      help: Trove enabled
                      default: 'n'
                      choices: ['y', 'n']

            - title: Cleanup
              options:
                  cleanup:
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      silent:
                        - "product-version"
