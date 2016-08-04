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
                      type: YamlFile
                      help: 'A YAML file representing the network configuration to be used. Please see "settings/provisioner/virsh/topology/network/network.sample.yml" as reference'
                      default: default.yml
                  topology-nodes:
                      type: Topology
                      help: Provision topology.
                      required: yes

            - title: cleanup
              options:
                  cleanup:
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      silent:
                          - image
