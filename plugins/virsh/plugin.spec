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
                      action: append
                      help: 'Address/FQDN of the BM hypervisor. Multiple hypervisors can be provided as a comma separated list'
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
                          Setting the custom MTU size on the provided physical networks of the Hypervisor. If the custom size is not
                          defined, the default MTU size of '1500' will be used.
                      default: False
                  host-network-mtu-size:
                      type: Value
                      help: |
                          Setting the custom MTU size on the provided virtual networks of the Hypervisor. This setting applies
                          custom MTU size on virtual network interfaces on the hypervisor and on network interfaces of virtual nodes.
                          If the custom size is not defined, the default MTU size of '1500' will be used.
                      default: False
                  host-network-multicast-querier:
                      type: Bool
                      help: |
                          Use this option in order to enable multicast querier on the external virtual network
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

                  pool-name:
                      type: Value
                      help: |
                        A name for the image pool. Default is 'images' as created by libvirt
                      default: "images"

                  image-mirror-url:
                      type: Value
                      help: |
                        URL to location where auxiliary images are placed.
                      default: https://url.corp.redhat.com/rhos-qe-mirror-tlv

                  image-ssh_user:
                      type: Value
                      default: root
                      help: |
                          Will be used as main ssh user for all ssh communtication.
                          User will not be created. If user should be created use
                          topology.username instead.

                  image-ansible_connection:
                      type: Value
                      default: ssh
                      help: |
                          Will set the ansible connection for all ansible operations.


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

                  topology-net-url:
                      type: Value
                      help: |
                          URL of network configuration to apply

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

            - title: Advanced Settings
              options:
                  serial-files:
                      type: Bool
                      default: False
                      help: |
                          Redirect the VMs serial output to files.
                          Files can be found under /var/lib/libvirt/qemu/{prefix-node_name-node_number}-serial.log
                          For example: /var/lib/libvirt/qemu/XYZ-undercloud-0-serial.log

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

                  vbmc-uninstall:
                      type: Bool
                      help: Tries to uninstall VBMC daemon using rpm and pip package mangers. Valid only if running 'cleanup=yes'.
                      default: False

            - title: Boot Mode
              options:
                  bootmode:
                      type: Value
                      help: |
                        Desired boot mode for VMs.
                        May require additional packages, please refer http://infrared.readthedocs.io/en/stable/advance_features.html#uefi-mode-related-binaries
                        NOTE: 'uefi' bootmode is supported only for nodes without OS.
                      choices: ['bios', 'uefi']
                      default: bios

            - title: Disk Bus
              options:
                  disk-bus:
                    type: Value
                    help: |
                      Desired bus to use for disks, please refer to: https://wiki.qemu.org/Features/VirtioSCSI
                      Some of disk busses supports different modes:
                    choices: ['virtio', 'scsi']
                    default: 'virtio'

            - title: Custom virt-install options
              options:
                  virtopts:
                    type: Value
                    help: |
                      Any custom options to be appended to virt-install command.
                      Usefull for special cases when one may want to override specific
                      options used for spawning vms (memballoon, rng and such).
                    default: ''
            - title: External VNC Mode
              options:
                  vnc-external:
                    type: Bool
                    help: |
                      Enable VNC console on all interfaces (0.0.0.0). Port will
                      be auto-allocated 5900,5901,...
                      Useful for debugging cases
                    default: False
                  vnc-password:
                    type: Value
                    help: |
                      Password to protect VNC console
                    required_when: >-
                      vnc-external == yes
            - title: ansible facts
              options:
                  collect-ansible-facts:
                      type: Bool
                      help: Save ansible facts as json file(s)
                      default: False

            - title: Snapshots
              options:
                  virsh-snapshot-create:
                      type: Bool
                      help: |
                          This will create snapshots of all virtual machines in the environment for use
                          with the `--virsh-snapshot-restore` flag.
                      default: False
                  virsh-snapshot-restore:
                      type: Bool
                      help: |
                          This will restore virtual machine snapshots created by the
                          `--virsh-snapshot-create` flag.
                      default: False
                  virsh-snapshot-name:
                      type: Value
                      help: |
                          The name to be used for the snapshot.
                      required_when:
                          - "virsh-snapshot-create == yes or virsh-snapshot-restore == yes"
                  virsh-snapshot-servers:
                       type: Value
                       help: |
                          A regular expression for the name of the virtual machine(s) to operate on. By
                          default it will operate on all virtual machines in the environment.
                       default: ".*"
                  virsh-snapshot-export:
                      type: Bool
                      help: |
                          This will shut down all virtual machines in the environment and export the
                          disks and environment configuration to the path provided by
                          ``--virsh-snapshot-path``.
                      default: False
                  virsh-snapshot-import:
                      type: Bool
                      help: |
                          This will import the virtual machine disks and environment configuration from
                          the path specified by ``--virsh-snapshot-path`` and start them up.
                      default: False
                  virsh-snapshot-path:
                      type: Value
                      help: |
                          The path to be used for the snapshot export, upload, download and import
                          processes. When doing a download, the basename of the path will be used
                          to determine which image set to download.
                      required_when: >-
                        virsh-snapshot-export == yes or
                        virsh-snapshot-import == yes or
                        virsh-snapshot-upload == yes or
                        virsh-snapshot-download == yes
                  virsh-snapshot-container:
                      type: Value
                      help: |
                          The object storage container/bucket to be used for the snapshot upload/download
                          process.
                      required_when: >-
                        virsh-snapshot-upload == yes or
                        virsh-snapshot-download == yes
                  virsh-snapshot-upload:
                      type: Bool
                      help: |
                          This will upload the image set found in the path specified by
                          ``--virsh-snapshot-path`` to the object storage container specified by
                          ``--virsh-snapshot-container``. For this to work with the AWS CLI, the
                          environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set,
                          with AWS_ENDPOINT_URL optionally set if a S3 compatible service is being used.
                      default: False
                  virsh-snapshot-download:
                      type: Bool
                      help: |
                          This flag enables/disables the download of an image set from object
                          storage using the container specified by ``--virsh-snapshot-container``
                          and the basename derived from ``--virsh-snapshot-path``. The folder
                          will be downloaded to the parent directory of ``--virsh-snapshot-path``.
                          For this to work with the AWS CLI, the environment variables AWS_ACCESS_KEY_ID
                          and AWS_SECRET_ACCESS_KEY must be set, with AWS_ENDPOINT_URL optionally set if
                          a S3 compatible service is being used.
                      default: False
                  virsh-snapshot-cleanup:
                      type: Bool
                      help: |
                          This is a flag to specify that the snapshot process should always remove
                          the path specified by ``--virsh-snapshot-path`` once it has completed
                          using the data. This is useful in a Continuous Integration (CI) environment
                          to ensure that the large amounts of data are not left behind on the host.
                      default: False
                  virsh-snapshot-quiesce:
                      type: Bool
                      help: |
                          This is a flag to enable a quiesce process after a snapshot restore or import.
                          This is useful to ensure that time is synchronised and services are all in the
                          correct state. This action must be done independently of the import process
                          because infrared will need to use the newly imported inventory.
                      default: False
