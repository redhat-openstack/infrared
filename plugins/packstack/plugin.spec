---
plugin_type: install
description: OpenStack installation using Packstack
subparsers:
    packstack:
        help: OpenStack installation using Packstack
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
                      type: Value
                      help: |
                          OpenStack network service
                      default: neutron
                      choices:
                          - neutron
                          - nova
                  network-variant:
                      type: Value
                      help: |
                          Default network backend used for tenant networks
                          __LISTYAMLS__
                      default: neutron_ml2-vxlan
                  public-network:
                      type: Bool
                      help: Deploy "public" external network on the Cloud as post-install.
                      default: yes
                  public-subnet:
                      type: Value
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
                          Enable usage of specified mirror (for rpm, pip etc) [brq,qeos,tlv - or hostname].
                          (Specified mirror needs to proxy multiple rpm source hosts and pypi packages.)
                      default: ''
                  version:
                      type: Value
                      help: The product version
                      required: yes
                      choices: ["7", "8", "9", "10", "11", "kilo", "liberty", "mitaka", "newton", "ocata"]
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

            - title: Patching options Menu
              options:
                  repos-patch:
                      type: Bool
                      help: |
                          Indicating `yes` instructs the undercloud installer to use temprorary patched_rpms.repo
                          that is created and copied to undercloud machine by the patch-components plugin.
                          The plugin usage instructions can be found at review.gerrithub.io/rhos-infra/patch-components
                      default: no
