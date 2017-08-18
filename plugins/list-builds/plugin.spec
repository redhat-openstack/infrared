plugin_type: other
subparsers:
    list-builds:
        description: List all the available puddle builds
        include_groups: ["Ansible options", "Common options"]
        options:
            base-url:
                type: Value
                help: The base url these puddles are stored
                default: https://url.corp.redhat.com/puddles
            version:
                type: Value
                help: Product version
                default: 12
            rhel-major-version:
                type: Value
                help: The rhel version
                default: 7
            subtype:
                type: Value
                help: The puddle subtype (opt, testing, director)
            file-output:
                type: Value
                help: |
                    Save the list to a file.
                    Path should be relative to the current working directory.

