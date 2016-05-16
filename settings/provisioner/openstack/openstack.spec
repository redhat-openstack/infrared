---
command:
    subcommands:
        - name: openstack
          help: Provision systems using Ansible OpenStack modules
          include_groups: ['Logging arguments', 'Inventory arguments', 'Common arguments', 'Configuration file arguments']
          groups:
            - name: cloud
              options:
                    - name: cloud
                      help: "The cloud which the OpenStack modules will operate against. Cloud setup instructions: http://docs.openstack.org/developer/os-client-config/#config-files"
                      required: yes
            - name: prefix
              options:
                    - name: prefix
                      help: An prefix which would be contacted to each provisioned resource. An random prefix would be generated in case this value is not specified.
            - name: keypair details
              options:
                    - name: key-file
                      help: The key file that would be uploaded to nova and injected into VMs upon creation.
                      default: ~/.ssh/id_rsa
                    - name: key-name
                      help: The name of the key that would be uploaded to nova and injected into VMs upon creation. If this option is missing, a public key would be generated from the key file and uploaded as a key_pair to the cloud
                      default: ''
            - name: image
              options:
                    - name: image
                      help: An image id or name, on OpenStack cloud to provision the instance with. To see full list of images avaialable on the cloud, use 'glance image-list'.
                      required: yes
            - name: dns
              options:
                    - name: dns
                      help: The dns server the provisioned instances should use.
                      default: 208.67.222.222
            - name: topology
              options:
                    - name: neutron
                      complex_type: YamlFile
                      help: Network resources
                      default: default.yml
                    - name: nodes
                      complex_type: Topology
                      help: Provision topology.
                      default: "controller:1"

            - name: Cleanup
              options:
                  - name: cleanup
                    action: store_true
                    help: Clean given system instead of running playbooks on a new one.
                    nested: no
                    silent:
                        - image
