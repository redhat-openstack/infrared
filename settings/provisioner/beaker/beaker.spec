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
            distro_tree:
                type: str
                help: Distro Tree ID
                default: 71576
