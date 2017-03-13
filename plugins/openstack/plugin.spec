---
plugin_type: provision
description: Provision systems using Ansible OpenStack modules
subparsers:
    openstack:
        help: Provision systems using Ansible OpenStack modules
        include_groups: ['Ansible options', 'Inventory', 'Common options', 'Answers file']
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

            - title: Topology
              options:
                  prefix:
                      type: Value
                      help: |
                          An prefix which would be concatenated to each provisioned resource.
                      default: ''
                  topology-network:
                      type: Value
                      help: |
                          Network resources
                          __LISTYAMLS__
                      default: 3_nets
                  topology-nodes:
                      type: KeyValueList
                      help: |
                          Provision topology.
                          List of of nodes types and their amount, in a "key:value" format.
                          Example: "--topology-nodes undercloud:1,controller:3,compute:2"
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
