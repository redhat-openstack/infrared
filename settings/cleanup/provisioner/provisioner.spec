subparsers:
    provisioner:
        help: Cleanups provisioned system
        include_groups: ["Ansible options", "Inventory options"]
        groups:
            - title: Settings
              options:
                  extra-vars:
                      action: append
                      short: e
                      help: Extra variables to be merged last
                      type: str
                      required: yes

            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook exec
