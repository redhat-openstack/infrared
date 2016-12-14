---
subparsers:
    virsh:
        include_groups: ["Ansible options", "Inventory options", "Common options", "Configuration file options"]
        formatter_class: RawTextHelpFormatter
        help: Provision systems using virsh
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
                  image:
                      type: YamlFile
                      help: |
                        (DEPRECATED)
                        The image to use for nodes provisioning.
                        Check the "sample.yml.example" for example.

                  image-url:
                      type: Value
                      help: |
                        URL to the image used for node provisioning.
                        Default is internal path for RHEL guest image
                      default: https://url.corp.redhat.com/images-rhel-guest-image-7-2-20160302-0-x86-64-qcow2

            - title: topology
              options:
                  topology-network:
                      type: ListOfYamls
                      help: 'Network topology. In the form of: <network>[,<network>] Example: net1,net2'
                      default: "data,external,management"
                  topology-nodes:
                      type: Topology
                      help: 'Provision topology. In the form of: <node>:<amount>[,<node>:<amount>] Example: undercloud:1,controller:3'
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
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      silent:
                          - image

            - title: boot_mode
              options:
                  boot_mode:
                      type: Value
                      help: |
                        Desired boot mode for VMs.
                        May require additional packages, please refer http://infrared.readthedocs.io/en/latest/advanced.html#uefi-mode-related-binaries
                      choices: ['hd', 'uefi']
                      default: hd
