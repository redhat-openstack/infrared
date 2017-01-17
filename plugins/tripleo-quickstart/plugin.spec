plugin_type: install
description: Backup and restore an undercloud machine
subparsers:
    tripleo-quickstart:
        help: Backup and restore an undercloud machine
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
                      help: |
                        Backup will create this file
                        Restore will use this file as source
                      default: "undercloud-quickstart.qcow2"

            - title: Tripleo User
              options:
                  user-name:
                      type: Value
                      help: The installation user name. Will be generated if missing
                      default: stack
