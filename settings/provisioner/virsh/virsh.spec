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
                      required: True
                  ssh-user:
                      type: str
                      help: User to SSH to the host with
                      default: root
                  ssh-key:
                      type: str
                      help: "User's SSH key"
                      default: '~/.ssh/id_rsa'
            - title: image
              options:
                  image-file:
                      type: str
                      help: An image to provision the host with
                      required: True
                  image-server:
                      type: str
                      help: Base URL of the image file server
                      required: True
            - title: topology
              options:
                  network:
                      type: str
                      help: Network
                      default: default.yml
                  topology:
                      type: str
                      help: 'Provision topology (default: __DEFAULT__)'
                      default: all-in-one.yml
            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook execution stage
                  cleanup:
                      action: store_true
                      help: Clean up environment at the end
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
