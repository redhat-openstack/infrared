---
subparsers:
    beaker:
        help: Provision systems using Beaker
        options:
            base-url:
                type: str
                help: Base URL of Beaker server
                required: True
            username:
                type: str
                help: 'Login username to authenticate to Beaker (default: __DEFAULT__)'
                default: admin
            password:
                type: str
                help: Password of login user
                required: True
            fqdn:
                type: str
                help: Fully qualified domain name of a system
                required: True
            action:
                type: str
                help: Action to perform
                required: True
                choices: [provision, release]
            distro-tree:
                type: str
                help: Distro Tree ID
                default: 71576
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
