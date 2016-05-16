---
command:
    subcommands:
        - name: virsh
          help: Provision systems using virsh
          include_groups: ['Ansible options', 'Inventory options', 'Common options', 'Configuration file options']
          groups:
              - name: Hypervisor
                options:
                    - name: host-address
                      help: 'Address/FQDN of the BM hypervisor'
                      required: yes
                    - name: host-user
                      help: 'User to SSH to the host with'
                      default: root
                    - name: host-key
                      help: "User's SSH key"
                      default: '~/.ssh/id_rsa'

              - name: Image
                options:
                    - name: image
                      complex_type: YamlFile
                      help: 'The image to use for nodes provisioning. Check the "sample.yml.example" for example.'
                      required: yes

              - name: Topology
                options:
                    - name: topology-network
                      complex_type: YamlFile
                      help: 'A YAML file representing the network configuration to be used. Please see "settings/provisioner/virsh/topology/network/network.sample.yml" as reference'
                      default: default.yml
                    - name: topology-nodes
                      complex_type: Topology
                      help: Provision topology.
                      default: "undercloud:1,controller:1,compute:1"

              - name: Cleanup
                options:
                    - name: cleanup
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      nested: no
                      silent:
                          - image
