---
config:
    plugin_type: install
    dependencies:
        - source: https://github.com/rhos-infra/infrared-common-libraries.git
subparsers:
    packstack:
        description: OpenStack installation using Packstack
        include_groups: ['Ansible options', 'Inventory', 'Common options', 'Answers file']
        groups:
            - title: Config
              options:
                  answer-file:
                      type: Value
                      help: Name for packstack answer file
                      default: 'packstack_config.txt'

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
                      type: VarFile
                      help: |
                          OpenStack network service
                          __LISTYAMLS__
                      default: neutron
                  network-variant:
                      type: VarFile
                      help: |
                          Default network backend used for tenant networks
                          __LISTYAMLS__
                      default: neutron_ml2-vxlan
                  network-gwhack:
                      type: Bool
                      help: |
                          Use the external gw IP on controllers interface, this can help if your cloud provider
                          has strict MAC filtering rules and you have just a simple setup.
                      default: 'no'
                  public-network:
                      type: Bool
                      help: Deploy "public" external network on the Cloud as post-install.
                      default: yes
                  public-subnet:
                      type: VarFile
                      help: |
                          Subnet detail for "public" external network on the OverCloud as post-install.
                          CIDR
                          Allocation Pool
                          Gateway
                          __LISTYAMLS__
                      default: default
                  # TODO(yfried): decouple this from openstack provisioner.

            - title: Product
              options:
                  mirror:
                      type: Value
                      help: |
                          Enable usage of specified mirror (for rpm, pip etc) [brq,rdu2,tlv - or hostname].
                          (Specified mirror needs to proxy multiple rpm source hosts and pypi packages.)
                      default: ''
                  version:
                      type: Value
                      help: The product version
                      required: yes
                      choices: ["6", "7", "8", "9", "10", "11", "12", "13", "juno", "kilo", "liberty", "mitaka", "newton", "ocata", "pike", "queens"]
                  build:
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
