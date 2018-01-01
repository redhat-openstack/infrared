---
config:
    plugin_type: provision
    dependencies:
        - source: https://github.com/rhos-infra/infrared-common-libraries.git
subparsers:
    virsh:
        description: Provision virtual machines on a single Hypervisor using libvirt
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Hypervisor
              options:
                  host-address:
                      type: Value
                      help: |
                          Address/FQDN of the BM hypervisor
                          Use "localhost" to use the localhost as Hypervisor
                      required: yes
                  host-user:
                      type: Value
                      help: 'User to SSH to the host with'
                      default: root
                  host-key:
                      type: Value
                      help: |
                           User's SSH key
                      default: null
                      required: true
                  host-validate:
                      type: Bool
                      help: |
                          Validate and enable virtualization on the hypervisor.
                          Disable this option if you already know your hypervisor support virtualization and that it
                          is enabled.
                      default: True
                  host-memory-overcommit:
                      type: Bool
                      help: |
                          By default memory overcommitment is false and provision will fail if Hypervisor's free
                          memory is lower than required memory for all nodes. Use `--host-mem-overcommitment True`
                          to change default behaviour.
                      default: False

            - title: image
              options:

                  image-url:
                      type: Value
                      help: |
                        URL to the image used for node provisioning.
                        Default is internal path for RHEL guest image
                      default: https://url.corp.redhat.com/rhel-guest-image-7-4-220-x86-64-qcow2

            - title: topology
              options:
                  prefix:
                      type: Value
                      help: |
                          Prefix VMs and networks names with this value.
                          Designed for cleanup improvement (clean only prefixed resources) and not for
                          several deployments on the same hypervisor.
                          Emty prefix on cleanup stage will cause deletion of all resources.
                      default: ir-

                  # fixme(yfried): add support for user files
                  topology-network:
                      type: VarFile
                      help: |
                          Network configuration to be used
                          __LISTYAMLS__
                      default: 3_nets

                  topology-nodes:
                      type: ListOfTopologyFiles
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
                  topology-extend:
                      type: Bool
                      default: False
                      help: |
                          Use it to extend existing deployment with nodes provided by topology.

            - title: cleanup
              options:
                  cleanup:
                      type: Bool
                      help: Clean given system instead of running playbooks on a new one.
                      # FIXME(yfried): setting default in spec sets silent=true always
                      # default: False
                      silent:
                          - topology-nodes

                  kill:
                      type: Bool
                      help: Destroy and undefine libvirt resources for the given workspace instead of running playbooks on a new one.
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
                        May require additional packages, please refer http://infrared.readthedocs.io/en/stable/advance_features.html#uefi-mode-related-binaries
                        NOTE: 'uefi' bootmode is supported only for nodes without OS.
                      choices: ['hd', 'uefi']
                      default: hd

            - title: ansible facts
              options:
                  collect-ansible-facts:
                      type: Bool
                      help: Save ansible facts as json file(s)
                      default: False
