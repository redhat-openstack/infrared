---
subparsers:
    virthost:
        include_groups: ["Ansible options", "Inventory options", "Common options", "Configuration file options"]
        formatter_class: RawTextHelpFormatter
        help: Prepare virthost machine for virsh provisioner
        groups:
            - title: Hypervisor
              options:
                  host-address:
                      type: Value
                      help: 'Address/FQDN of the BM hypervisor'
                      required: yes
                  host-user:
                      type: Value
                      help: 'User to SSH to the host with'
                      default: root
                  host-key:
                      type: Value
                      help: "User's SSH key"
                      required: yes
            - title: Preparation for OpenStack TripleO
              options:
                  openstack-prepare:
                      type: Value
                      choices: ['yes', 'no']
                      default: 'yes'
                      help: |
                          Set this to "no" if You do NOT need virthost to be prepared
                          for virsh+ospd deployment (e.g ipxe-ssh) - atm means
                          when you are not going to use it with rest of InfRared.
                  openstack-user-name:
                      type: Value
                      help: The installation user name
                      default: stack
                  openstack-user-password:
                      type: Value
                      help: The installation user password
                      default: stack

