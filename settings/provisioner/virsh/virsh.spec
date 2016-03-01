---
subparsers:
    virsh:
        help: Provision systems using 'virsh'
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
            network:
                type: str
                help: Network
                default: default.yml
            image-file:
                type: str
                help: An image to provision the host with
                required: True
            image-server:
                type: str
                help: Base URL of the image file server
                required: True
            topology:
                type: str
                help: 'Provision topology (default: __DEFAULT__)'
                default: all-in-one.yml
            dry-run:
                action: store_true
                help: Only generate settings, skip the playbook execution stage
            cleanup:
                action: store_true
                help: Clean up environment at the end
            input-files:
                action: append
                type: str
                help: Settings file to be merged first
                short: n
            output-file:
                type: str
                short: o
                help: 'Name for the generated settings file (default: stdout)'
            extra-vars:
                action: append
                short: e
                help: Extra variables to be merged last
                type: str
