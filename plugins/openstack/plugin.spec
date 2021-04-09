---
config:
    plugin_type: provision
subparsers:
    openstack:
        description: Provision systems using Ansible OpenStack modules
        include_groups: ['Ansible options', 'Inventory', 'Common options', 'Common variables', 'Answers file']
        groups:
            - title: OpenStack Cloud Details
              options:
                  cloud:
                      type: Value
                      help: "The cloud which the OpenStack modules will operate against. Cloud setup instructions: http://docs.openstack.org/developer/os-client-config/#config-files"
                      required: yes
                  key-file:
                      type: Value
                      help: The key file that would be uploaded to nova and injected into VMs upon creation.
                      default: ~/.ssh/id_rsa
                  key-name:
                      type: Value
                      help: The name of the key that would be uploaded to nova and injected into VMs upon creation. If this option is missing, a public key would be generated from the key file and uploaded as a key_pair to the cloud
                      default: ''
                  dns:
                      type: ListValue
                      help: |
                          DNS servers the provisioned instances should use.
                          comma separated list.
                      default: 208.67.222.222
                  anti-spoofing:
                      type: Bool
                      default: true
                      help: |
                          Controls whether security groups and port_security_enabled=True (anti-spoofing rules) are applied.
                          Disable in case arbitary MAC and IP addresses need to reach outside assigned ports
                          (e.g. useful for OpenStack in OpenStack deployments). Disabling this will also set security_groups
                          to None.
                  os-server-timeout:
                      type: Value
                      default: 360
                      help: |
                          Number of seconds to wait for os_server module commands, defaults to 240 instead of
                          ansible default value of 180 which proved to be too small quite often.
            - title: Topology
              options:
                  prefix:
                      type: Value
                      help: |
                          An prefix which would be concatenated to each provisioned resource.
                      default: ''
                  topology-network:
                      type: VarFile
                      help: |
                          Network resources
                          __LISTYAMLS__
                      default: 3_nets
                  provider-network:
                      type: Value
                      help: |
                          Provider network name to use for external connectivity
                  topology-nodes:
                      type: ListOfTopologyFiles
                      help: |
                          Provision topology.
                          List of of nodes types and their amount, in a "key:value" format.
                          Example: "--topology-nodes undercloud:1,controller:3,compute:2"

                          To override node parameters the extra args can be provided in the format:
                          -e override.controller.memory=30720
                          __LISTYAMLS__
                      default: "aio:1"
                  image:
                      type: Value
                      help: |
                          An image id or name, on OpenStack cloud to provision the instance with. To see full list of images available on the cloud, use 'glance image-list'.
                          Note: the specific image for a node can be assigned using extra var argument: '-e provisioner.nodes.tester.image=custom_image_name
                      required: yes
                  username:
                      type: Value
                      help: default username for nodes
                      default: "cloud-user"

            - title: cleanup
              options:
                  cleanup:
                      type: Bool
                      help: Clean given system instead of running playbooks on a new one.
                      silent:
                          - image

            - title: Setup BMC node repositories
              options:
                  bmc-cdn:
                      type: FileValue
                      help: |
                          YAML file
                          Register the BMC node with a Red Hat Subscription Management platform.
                          see documentation for more details

                  bmc-version:
                      type: Value
                      help: |
                          The product version (product == director) that will be installed on BMC node
                          Numbers are for OSP releases
                          Names are for RDO releases
                      choices:
                        - "7"
                        - "8"
                        - "9"
                        - "10"
                        - "11"
                        - "12"
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                        - pike
