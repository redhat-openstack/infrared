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
#                  topology-network:
#                      type: YamlFile
#                      help: 'A YAML file representing the network configuration to be used. Please see "settings/provisioner/virsh/topology/network/network.sample.yml" as reference'
#                      default: default.yml
                  topology-nodes:
                      type: KeyValueList
                      help: |
                          Provision topology.
                          List of of nodes types and they amount, in a "key=value" format.
                          Example: "'--topology-nodes 'undercloud=1;controller=3;compute=2'"
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

            - title: boot_mode
              options:
                  boot_mode:
                      type: Value
                      help: |
                        Desired boot mode for VMs.
                        May require additional packages, please refer http://infrared.readthedocs.io/en/latest/advanced.html#uefi-mode-related-binaries
                      choices: ['hd', 'uefi']
                      default: hd
