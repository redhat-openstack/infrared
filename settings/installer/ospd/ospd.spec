---
subparsers:
    ospd:
        help: Install OpenStack using OSP-d installer
        options:
            dry-run:
                action: store_true
                help: Only generate settings, skip the playbook execution stage
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
        groups:
              - title: Product details
                description: |
                    Version and build of the procuct. use "core-*" to specify
                    core version and build.
                options:
                    version:
                        required: true
                        type: str
                        help: OSPd version [7, 7.3, 8, ...]
                    build:
                        type: str
                        default: ""
                        help: |
                            Specific puddle/poodle selection.
                            This can be a known-symlink (Y1, Z1, GA, etc.), or
                            a puddle date stamp in the form of YYYY-MM-DD.X
                            If specifiec, will override minor version.
                            If not specified, will default to latest.
                    core-version:
                        type: str
                        help: Use a different version of core bits. defaults to "version"
                    core-build:
                        type: str
                        help: |
                            Use a different build of core bits. defaults to "build".
                            If "core-version" is specified, defaults to "latest"
              - title: network
                description: Network configuration details for the Overcloud networks
                options:
                    network-protocol:
                        choices: [ipv4, ipv6]
                        help: IP version for network
                        default: ipv4
                    network-template:
                        help: |
                            Network configuration template file. Search first in template dir.
                            (default: <settings_dir>/network/templates/__DEFAULT__)
                        default: ipv4.yml
                    ssl:
                        choices: ["yes", "no"]
                        help: Use SSL
                        default: "no"
                    network-isolation:
                        choices: ["yes", "no"]
                        help: Use Network Isolation
                        default: "no"
                    network-variant:
                        choices: [gre, vxlan, sriov, vlan]
                        default: vxlan
              - title: Image Options
                options:
                    image-server:
                        type: str
                        help: URL to images servers
              - title: Storage Options
                options:
                    storage-type:
                        choices: [internal, external]
                        default: internal
                        help: |
                            Use internal/external storage
                    storage-template:
                        help: |
                            Storage configuration template file. Search first in templates dir.
                            (default: match storage type)

