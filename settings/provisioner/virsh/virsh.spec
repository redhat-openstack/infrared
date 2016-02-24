---

options:
    verbose:
        help: 'Verbosity level'
        short: v
        action: count
        default: 0

subparsers:
    virsh:
        help: Provision systems using 'virsh'
        options:
            hypervisor:
                type: str
                help: Hypervisor
                choices: [default]
                required: True
            network:
                type: str
                help: Network
                choices: [default]
                default: default
            image:
                type: str
                help: An image to provision the systems with
                choices: [rhel]
                default: rhel
            topology:
                type: str
                help: 'Provision topology (default: __DEFAULT__)'
                default: all-in-one
                choices: [
                    all-in-one,
                    multi-node,
                    ospd_1ctrl_1cmpt,
                    ospd_1cont_1comp_1ceph,
                    ospd_3cont_1comp,
                    ospd_3cont_1comp_1ceph,
                    ospd_3cont_1comp_3ceph,
                    ospd_3cont_2comp,
                    ospd_3cont_2comp_3ceph,
                    ]
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
