---
plugin_type: provision
description: Provision systems using Foreman
subparsers:
    foreman:
        help: Provision systems using Foreman
        include_groups: ['Ansible options', 'Inventory', 'Common options', 'Answers file']
        groups:
            - title: Foreman server
              options:
                  url:
                      type: Value
                      help: 'The Foreman api url'
                      required: True
                  user:
                      type: Value
                      help: 'User to Forman server'
                      required: True
                  password:
                      type: Value
                      help: 'Password of Forman server'
                      required: True
                  strategy:
                      type: Value
                      help: 'Whether to use Foreman or system ipmi command.'
                      default: foreman
                  action:
                      type: Value
                      help: 'Which command to send with the power-management selected by mgmt_strategy. For example - reset, reboot, cycle'
                      default: cycle
                  wait:
                      type: Value
                      choices: ['yes', 'no']
                      default: 'yes'
                      help: 'Wait for host to return from rebuild'

            - title: Host details
              options:
                  host-address:
                      type: Value
                      help: 'Name or ID of the host as listed in foreman'
                      required: yes
                  host-user:
                      type: Value
                      help: 'User to SSH to the host with'
                      default: root
                  host-password:
                      type: Value
                      help: "User's SSH password"
                  host-key:
                      type: Value
                      help: "User's SSH key"
                  host-ipmi-username:
                      type: Value
                      help: "Host IPMI username"
                  host-ipmi-password:
                      type: Value
                      help: "Host IPMI password"
