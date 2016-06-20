subparsers:
    provisioner:
        formatter_class: RawTextHelpFormatter
        help: Cleanups provisioned system
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
