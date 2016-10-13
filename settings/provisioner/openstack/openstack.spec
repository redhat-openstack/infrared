---
subparsers:
    openstack:
        help: Provision systems using Ansible OpenStack modules
        include_groups: ['Ansible options', 'Inventory options', 'Common options', 'Configuration file options']
        groups:
            - title: cloud
              options:
                  cloud:
                      type: Value
                      help: "The cloud which the OpenStack modules will operate against. Cloud setup instructions: http://docs.openstack.org/developer/os-client-config/#config-files"
                      required: yes
            - title: prefix
              options:
                  prefix:
                      type: Value
                      help: An prefix which would be contacted to each provisioned resource. An random prefix would be generated in case this value is not specified.
            - title: keypair details
              options:
                  key-file:
                      type: Value
                      help: The key file that would be uploaded to nova and injected into VMs upon creation.
                      default: ~/.ssh/id_rsa
                  key-name:
                      type: Value
                      help: The name of the key that would be uploaded to nova and injected into VMs upon creation. If this option is missing, a public key would be generated from the key file and uploaded as a key_pair to the cloud
                      default: ''
            - title: image
              options:
                  image:
                      type: Value
                      help: |
                          An image id or name, on OpenStack cloud to provision the instance with. To see full list of images available on the cloud, use 'glance image-list'.
                          Note: the specific image for a node can be assigned using extra var argument: '-e provisioner.nodes.tester.image=custom_image_name
                      required: yes
            - title: dns
              options:
                  dns:
                      type: Value
                      help: The dns server the provisioned instances should use.
                      default: 208.67.222.222
            - title: topology
              options:
                  neutron:
                      type: YamlFile
                      help: Network resources
                      default: default.yml
                  nodes:
                      type: Topology
                      help: Provision topology.
                      default: "controller:1"

            - title: cleanup
              options:
                  cleanup:
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      nested: no
                      silent:
                          - image
