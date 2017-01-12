plugin_type: install
description: backup and restore an undercloud machine
subparsers:
    tripleo-quickstart:
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Quickstart Menu
              options:
                  quickstart:
                      type: Value
                      help: |
                        let us choose between quickstart back and restore
                      choices:
                          - backup
                          - restore
                      required: true

                  filename:
                      type: Value
                      help: Absolute path to the filename
                      required: true

            - title: Tripleo User
              options:
                  user-name:
                      type: Value
                      help: The installation user name. Will be generated if missing
                      default: stack
