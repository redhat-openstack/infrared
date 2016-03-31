---
subparsers:
    foreman:
        help: Provision systems using 'foreman'
        groups:
            - title: foreman
              options:
                  user:
                      type: Value
                      help: User to Forman server
                      required: True
                  password:
                      type: Value
                      help: Password of Forman server
                      required: True
                  url:
                      type: Value
                      help: The Foreman api url
                      required: True
                  strategy:
                      type: Value
                      help: Whether to use Foreman or system ipmi command.
                      default: foreman
                  action:
                      type: Value
                      help: Which command to send with the power-management selected by mgmt_strategy. For example - reset, reboot, cycle
                      default: cycle
                  wait:
                      type: Value
                      default: true
                      help: Whether we should wait for the host given the 'rebuild' state was set.
            - title: host
              options:
                  host-address:
                      type: Value
                      help: Name or ID of the host as listed in foreman
                      required: yes
                  host-key:
                      type: Value
                      help: "User's SSH key"
                      default: ~/.ssh/id_rsa
            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook execution stage
                  cleanup:
                      action: store_true
                      help: Provision the host using Forman
                      required: True
                  input:
                      action: append
                      type: str
                      help: Settings file to be merged first
                      short: n
                  output:
                      type: str
                      short: o
                      help: 'Name for the generated settings file (default: stdout)'
                  extra-vars:
                      action: append
                      short: e
                      help: Extra variables to be merged last
                      type: str
