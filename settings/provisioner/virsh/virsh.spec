---
subparsers:
    virsh:
        formatter_class: RawTextHelpFormatter
        help: Provision systems using virsh
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
                      default: '~/.ssh/id_rsa'

            - title: image
              options:
                  image:
                      type: YamlFile
                      help: 'The image to use for nodes provisioning. Check the "sample.yml.example" for example.'
                      required: yes

            - title: topology
              options:
                  topology-network:
                      type: YamlFile
                      help: 'A YAML file representing the network configuration to be used. Please see "settings/provisioner/virsh/topology/network/network.sample.yml" as reference'
                      default: default.yml
                  topology-nodes:
                      type: Topology
                      help: Provision topology.
                      default: "undercloud:1,controller:1,compute:1"

            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook execution stage
                  cleanup:
                      action: store_true
                      help: Clean given system instead of provisioning a new one
                  input:
                      action: append
                      type: str
                      short: i
                      help: Input settings file to be loaded before the merging of user args
                  output:
                      type: str
                      short: o
                      help: 'File to dump the generated settings into (default: stdout)'
                  extra-vars:
                      action: append
                      short: e
                      help: Extra variables to be merged last
                      type: str
                  from-file:
                      type: IniFile
                      help: the ini file with the list of arguments
                  generate-conf-file:
                      type: str
                      help: generate configuration file (ini) containing default values and exits. This file is than can be used with the from-file argument
                  ansible-args:
                      help: |
                        Extra variables for ansible-playbook tool
                        Should be specified as a list of ansible-playbook options, separated with commas.
                        For example, --ansible-args="tags=overcloud,forks=500"
                      type: AdditionalArgs
