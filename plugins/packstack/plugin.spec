---
plugin_type: install
description: OpenStack installation using Packstack
subparsers:
    packstack:
        help: OpenStack installation using Packstack
        include_groups: ['Ansible options', 'Inventory', 'Common options', 'Answers file']
        groups:
            - title: Storage
              options:
                  storage:
                      type: Value
                      help: |
                          Storage
                          __LISTYAMLS__
                  storage-backend:
                      type: Value
                      help: |
                          Storage backend
                          __LISTYAMLS__

            - title: Config
              options:
                  config:
                      type: Value
                      help: |
                          Packstack Configuration
                          __LISTYAMLS__
                      default: default

            - title: Debug
              options:
                  osdebug:
                      type: Bool
                      help: Install OS with DEBUG
                      default: 'yes'


            - title: Messaging
              options:
                  messaging-variant:
                      type: Value
                      help: Messaging type
                      default: rabbitmq
                      choices: ["rabbitmq", "qpid"]

            - title: Network
              options:
                  network-service:
                      type: Value
                      help: |
                          Network
                          __LISTYAMLS__
                      default: neutron
                  network-variant:
                      type: Value
                      help: |
                          Network variant
                          __LISTYAMLS__
                      default: neutron_ml2-vxlan
                  public-network:
                      type: Bool
                      help: Deploy "public" external network on the Cloud as post-install.
                      default: 'yes'
                  public-subnet:
                      type: Value
                      help: |
                          Subnet detail for "public" external network on the OverCloud as post-install.
                          CIDR
                          Allocation Pool
                          Gateway

                          If empty, will try to discover using "neutron.subnets.external" details
                  # TODO(yfried): decouple this from openstack provisioner.

            - title: Product
              options:
                  mirror:
                      type: Value
                      help: |
                          Enable usage of specified mirror (for rpm, pip etc) [brq,qeos,tlv - or hostname].
                          (Specified mirror needs to proxy multiple rpm source hosts and pypi packages.)
                      default: ''
                  product-version:
                      type: Value
                      help: The product version
                      required: yes
                      choices: ["7", "8", "9", "10", "11", "kilo", "liberty", "mitaka", "newton", "ocata"]
                  product-build:
                      type: Value
                      help: The product build
                      default: latest

            - title: Extra components
              options:
                  component-sahara:
                      type: Bool
                      help: Sahara enabled
                      default: 'no'
                  component-trove:
                      type: Bool
                      help: Trove enabled
                      default: 'no'

            - title: Cleanup
              options:
                  cleanup:
                      type: Bool
                      help: Clean given system instead of running playbooks on a new one.
                      silent:
                        - "product-version"
