---
plugin_type: provision
description: Provision systems using Ansible OpenStack modules
subparsers:
    openstack:
        help: Provision systems using Ansible OpenStack modules
        include_groups: ['Ansible options', 'Inventory', 'Common options', 'Answers file']
        groups:
            - title: cloud
              options:
                  cloud:
                      type: Value
                      help: "The cloud which the OpenStack modules will operate against. Cloud setup instructions: http://docs.openstack.org/developer/os-client-config/#config-files"
                      required: yes
                  prefix:
                      type: Value
                      help: |
                          An prefix which would be concatenated to each provisioned resource.
                      default: ''
            - title: dns
              options:
                  dns:
                      type: Value
                      help: The dns server the provisioned instances should use.
                      default: 208.67.222.222
            - title: topology
              options:
                  topology-network:
                      type: Value
                      help: |
                          Network resources
                          __LISTYAMLS__
                      default: 3_nets

            - title: cleanup
              options:
                  cleanup:
                      type: Bool
                      help: Clean given system instead of running playbooks on a new one.
