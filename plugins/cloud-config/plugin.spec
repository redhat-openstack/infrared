---
plugin_type: install
subparsers:
    cloud-config:
        description: Collection of overcloud configuration tasks
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Tasks Control
              options:
                  tasks:
                      type: ListOfFileNames
                      help: |
                          Provide a option to run one or more tasks to the cloud. If you run two or more tasks
                          at once, you need to separate them with commas
                          Example: infrared cloud-config --task task1,task3,task2
                          Note: Tasks represent playbooks, which are stored in the 'lookup_dir' folder in plugin
                          directory. Task run in the same order as they are provided.
                      lookup_dir: 'post_tasks'
                      required: yes

            - title: Service Discovery
              options:
                  resync:
                      type: Bool
                      help: |
                          Whether we need to resync services.
                          Used with service discovery.
                      default: False

            - title: External Network
              options:
                  deployment-files:
                      type: Value
                      help: |
                          Name of folder in cloud's user on undercloud, which containing the templates of
                          the overcloud deployment.

                  network-protocol:
                      type: Value
                      help: The overcloud network backend.
                      default: ipv4
                      choices:
                          - ipv4
                          - ipv6

                  public-subnet:
                      type: VarFile
                      help: |
                          Subnet detail for "public" external network on the overcloud as post-install.
                          (CIDR, Allocation Pool, Gateway)
                          __LISTYAMLS__
                      default: default_subnet
            - title: Scale down nodes
              options:
                  node-name:
                      type: Value
                      help: |
                        Name of the node to remove

            - title: Scale up nodes
              options:
                 scale-nodes:
                      type: ListValue
                      help: |
                            List of compute nodes to be added.
                            Example: compute-3,compute-4,compute-5

            - title: Ironic Configuration
              options:
                  vbmc-username:
                      type: Value
                      default: admin
                      help: |
                        VBMC username (Necessary when Ironic's driver is 'pxe_ipmitool' - OSP >= 11)
                  vbmc-password:
                      type: Value
                      default: password
                      help: |
                        VBMC password (Necessary when Ironic's driver is 'pxe_ipmitool' - OSP >= 11)