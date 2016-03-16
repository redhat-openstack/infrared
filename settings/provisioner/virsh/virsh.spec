---
subparsers:
    virsh:
        help: Provision systems using virsh
        groups:
            - title: host
              options:
                  host:
                      type: str
                      help: Address/FQDN of the BM hypervisor
                      required: yes
                  ssh-user:
                      type: str
                      help: User to SSH to the host with
                      default: root
                      required: yes
                  ssh-key:
                      type: str
                      help: "User's SSH key"
                      default: ~/.ssh/id_rsa
                      required: yes
            - title: image
              options:
                  image-file:
                      type: str
                      help: An image to provision the host with
                      required: yes
                  image-server:
                      type: str
                      help: Base URL of the image file server
                      required: yes
            - title: topology
              options:
                  network:
                      type: str
                      help: Network
                      default: default.yml
                      required: yes
                  topology:
                      type: str
                      help: Provision topology.
                      default: "1_controller,1_compute,1_undercloud"
                      required: yes
            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook execution stage
                  cleanup:
                      action: store_true
                      help: Clean given system instead of provisioning a new one
                      requires_only: [host, ssh-user,  ssh-key, topology]
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
                      help: generate configuration file (ini) containing default values and exits. This file is than can be used wit the from-file argument
