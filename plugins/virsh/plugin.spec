plugin_type: provision
description: Provisioner virtual machines on a single Hypervisor using libvirt
subparsers:
    virsh:
        # FIXME(yfried): duplicates "description"
        help: Provisioner virtual machines on a single Hypervisor using libvirt
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
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
                  host-validate:
                      type: Bool
                      help: |
                          Validate and enable virtualization on the hypervisor.
                          Disable this option if you already know your hypervisor support virtualization and that it
                          is enabled.
                      default: True

            - title: image
              options:

                  image-url:
                      type: Value
                      help: |
                        URL to the image used for node provisioning.
                        Default is internal path for RHEL guest image
                      default: https://url.corp.redhat.com/rhel-guest-image-7-3-35-x86-64-qcow2

            - title: topology
              options:
                  # fixme(yfried): add support for user files
                  topology-network:
                      type: Value
                      help: |
                          Network configuration to be used
                          __LISTYAMLS__
                      default: 3_nets

                  topology-nodes:
                      type: KeyValueList
                      help: |
                          Provision topology.
                          List of of nodes types and they amount, in a "key:value" format.
                          Example: "'--topology-nodes 'undercloud:1,controller:3,compute:2'"
                          __LISTYAMLS__
                      required: yes
                  topology-username:
                      type: Value
                      default: cloud-user
                      help: |
                          Non-root username with sudo privileges that will be created on nodes.
                          Will be use as main ssh user subsequently.


            - title: cleanup
              options:
                  cleanup:
                      type: Bool
                      help: Clean given system instead of running playbooks on a new one.
                      # FIXME(yfried): setting default in spec sets silent=true always
                      # default: False
                      silent:
                          - topology-nodes

            - title: Boot Mode
              options:
                  bootmode:
                      type: Value
                      help: |
                        Desired boot mode for VMs.
                        May require additional packages, please refer http://infrared.readthedocs.io/en/latest/advanced.html#uefi-mode-related-binaries
                      choices: ['hd', 'uefi']
                      default: hd
