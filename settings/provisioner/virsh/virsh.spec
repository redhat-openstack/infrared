---
subparsers:
    virsh:
        help: Provision systems using virsh
        groups:
            - title: Hypervisor
              options:
                  host-address:
                      type: Value
                      help: Address/FQDN of the BM hypervisor
                      required: yes
                  host-user:
                      type: Value
                      help: User to SSH to the host with
                      default: root
                  host-key:
                      type: Value
                      help: "User's SSH key"
                      default: ~/.ssh/id_rsa
            - title: image
              options:
                  image:
                      type: YamlFile
                      help: The RHEL distribution version
                      required: yes
            - title: topology
              options:
                  topology-network:
                      type: YamlFile
                      help: Network
                      default: default.yml
                  topology-nodes:
                      type: Topology
                      help: Provision topology.
                      default: "1_controller,1_compute,1_undercloud"
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
