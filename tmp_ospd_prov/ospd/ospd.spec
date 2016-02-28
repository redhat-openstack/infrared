---
options:
    verbose:
        help: 'Verbosity level'
        short: v
        action: count
        default: 0

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
