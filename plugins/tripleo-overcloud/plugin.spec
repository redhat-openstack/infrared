---
plugin_type: install
description: Install a Tripleo overcloud using a designated undercloud node
subparsers:
    tripleo-overcloud:
        # FIXME(yfried): duplicates "description"
        help: Install a Tripleo overcloud using a designated undercloud node
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Deployment Description
              options:
                  deployment-files:
                      type: Value
                      help: |
                          The absolute path to the folder containing the templates of the overcloud deployment.
                          Please see `settings/installer/ospd/deployment/example` as reference.
                          Use "virt" to enable preset templates for virtual POC environment.
                      required: yes

                  instackenv-file:
                      type: Value
                      help: The path to the instackenv.json configuration file used for introspection.

                  version:
                      type: Value
                      help: |
                          The product version (product == director)
                          Numbers are for OSP releases
                          Names are for RDO releases
                      choices:
                        - "7"
                        - "8"
                        - "9"
                        - "10"
                        - "11"
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                      required: true

                  controller-nodes:
                      type: Value
                      help: The amount of controller nodes to deploy

                  compute-nodes:
                      type: Value
                      help: The amount of compute nodes to deploy

                  storage-nodes:
                      type: Value
                      help: |
                            The amount of storage nodes to deploy. If --storage-backend is set, this
                            value will default to '1', otherwise no storage nodes will be used.

            - title: Overcloud Options
              options:
                  overcloud-debug:
                      type: Bool
                      default: yes
                      help: Specifies whether overcloud service should enable debug mode

                  overcloud-ssl:
                      type: Bool
                      default: no
                      help: Specifies whether ths SSL should be used for overcloud

                  overcloud-script:
                      type: Value
                      help: |
                            The absolute path to a custom overcloud deployment script.
                            If not set, it will auto generate a deployment according to the
                            provided templates / options.

                  overcloud-templates:
                      type: Value
                      help: |
                            Add extra environment template files to "overcloud deploy" command
                            File (in YAML format) containing a list of paths to template files on the UnderCloud.
                            NOTE: Omit this to not include any extra files, or use "none"
                            __LISTYAMLS__

            - title: Network Configuration
              options:
                  network-backend:
                      type: Value
                      help: The overcloud network backend.
                      choices:
                          - gre
                          - vxlan
                          - vlan
                      default: vxlan

                  network-protocol:
                      type: Value
                      help: The overcloud network backend.
                      default: ipv4
                      choices:
                          - ipv4
                          - ipv6

                  network-lbaas:
                      type: Bool
                      default: no
                      help: Activate Neutron LBaaS(v2) extension on the overcloud.

                  network-dvr:
                      type: Bool
                      default: no
                      help: Activate Neutron DVR extension on the overcloud.

            - title: Overcloud Public Network
              options:
                  public-network:
                      type: Bool
                      default: yes
                      help: Deploy "public" external network on the overcloud as post-install.

                  public-subnet:
                      type: Value
                      help: |
                          Subnet detail for "public" external network on the overcloud as post-install.
                          (CIDR, Allocation Pool, Gateway)
                          __LISTYAMLS__
                      default: default_subnet

                  public-vlan:
                      type: Bool
                      default: no
                      help: |
                          Set this to "yes" if overcloud's external network is on a VLAN that's unreachable from the
                          undercloud.
                          This will configure network access from UnderCloud to overcloud's API/External(floating ips)
                          network, creating a new VLAN interface connected to ovs's "br-ctlplane" bridge.
                          NOTE: If your UnderCloud's network is already configured properly, this could disrupt it, making overcloud API unreachable
                          For more details, see: "VALIDATING THE OVERCLOUD" on https://access.redhat.com/documentation/en/red-hat-openstack-platform/10-beta/paged/director-installation-and-usage/chapter-6-performing-tasks-after-overcloud-creation

            - title: Overcloud storage
              options:
                  storage-external:
                      type: Bool
                      help: Whether to use an external storage rather than setting it up with the director
                      default: no

                  storage-backend:
                      type: Value
                      choices:
                          - ceph
                          - swift
                          - netapp-iscsi
                          - netapp-nfs
                          - lvm
                      default: 'lvm'
                      help: |
                        The storage that we would like to use.
                        If not supplied, OSPD will default to local LVM on the controllers.
                        NOTE: when not using external storage, this will set the default for "--storage-nodes" to 1.
