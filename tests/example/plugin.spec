plugin_type: provision
description: Example provisioner plugin
subparsers:
    example:
        # FIXME(yfried): duplicates "description"
        help: Example provisioner plugin
        include_groups: ["Ansible options", "Inventory options", "Common options", "Answers file"]
        groups:
            - title: Group A
              options:
                  foo-bar:
                      type: Value
                      help: "foo.bar option"
                      default: "default string"
