---
subparsers:
    openstack:
        include_groups: ["Ansible options", "Inventory options", "Common options", "Configuration file options"]
        formatter_class: RawTextHelpFormatter
        help: Provision systems using Ansible OpenStack modules
        groups:
            - title: cloud
              options:
                  cloud:
                      type: Value
                      help: "The cloud which the OpenStack modules will operate against. Cloud setup instructions: http://docs.openstack.org/developer/os-client-config/#config-files"
                      required: yes

            - title: image
              options:
                  image:
                      type: YamlFile
                      help: |
                        The image to use for nodes provisioning.
                        Check the "sample.yml.example" for example.
                      default: rhel-7.3.yml

            - title: topology
              options:
                  topology-network:
                      type: ListOfYamls
                      help: 'Network topology. In the form of: <network>[,<network>] Example: net1,net2'
                      default: "data,external,management"

                  topology-routers:
                      type: YamlFile
                      help: 'A YAML file representing the router configuration to be used.'
                      default: default.yml

                  topology-nodes:
                      type: Topology
                      help: 'Provision topology. In the form of: <node>:<amount>[,<node>:<amount>] Example: undercloud:1,controller:3'
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

            - title: cleanup
              options:
                  cleanup:
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      nested: no
                      silent:
                          - image
