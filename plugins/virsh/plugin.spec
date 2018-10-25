---
config:
    plugin_type: provision
subparsers:
    virsh:
        description: Provision virtual machines on a single Hypervisor using libvirt
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
                  host-memory-overcommit:
                      type: Bool
                      help: |
                          By default memory overcommitment is false and provision will fail if Hypervisor's free
                          memory is lower than required memory for all nodes. Use `--host-mem-overcommitment True`
                          to change default behaviour.
                      default: False
                  host-mtu-size:
                      type: Value
                      help: |
                          Setting the custom MTU size on the provided networks of the Hypervisor. If the custom size is not defined,
                          the default MTU size of '1500' will be used.
                      default: False

            - title: image
              options:

                  image-url:
                      type: Value
                      help: |
                        URL to the image used for node provisioning.
                        Default url to RHEL 7.6 guest image
                        RHEL 7.6 is unavailable for OSP7 and OSP11
                      default: https://url.corp.redhat.com/rhel-guest-image-7-6-210-x86-64-qcow2

                  force-image-download:
                      type: Bool
                      help: |
                        Forces downloading the image.
                        If 'False' (default), the image won't be downloaded if one already exists on the destination
                      default: False

                  disk-pool:
                      type: Value
                      help: |
                        A path to the image pool. Default is Storage Pool from libvirt
                      default: "/var/lib/libvirt/images"

            - title: topology
              options:
                  prefix:
                      type: Value
                      help: |
                          Prefix VMs and networks names with this value. If this value is
                          more than 4 characters long some resources like bridges will fail
                          to create due to name lengths limit.
                      length: 4

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

                  topology-timezone:
                      type: Value
                      help: |
                          If provided infrared will set specific timezone for the topology. Value
                          has to be a valid timezone.
                          None: Option change Hypervisor Timezone also

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

                  remove-nodes:
                      type: ListValue
                      help: |
                          Use it to remove nodes from existing topology.
                          Example: compute-3,compute-4,compute-5

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

            - title: Disk Bus
              options:
                  disk-bus:
                    type: Value
                    help: |
                      Desired bus to use for disks, please refer to: https://wiki.qemu.org/Features/VirtioSCSI
                      Some of disk busses supports different modes:
                    choises: ['virtio', 'scsi']
                    default: 'virtio'

            - title: ansible facts
              options:
                  collect-ansible-facts:
                      type: Bool
                      help: Save ansible facts as json file(s)
                      default: False
