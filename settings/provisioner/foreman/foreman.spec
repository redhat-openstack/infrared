---
subparsers:
    foreman:
        help: Provision systems using Foreman
        include_groups: ['Ansible options', 'Inventory options', 'Common options', 'Configuration file options']
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
                      default: true
                      help: 'Whether we should wait for the host given the "rebuild" state was set.'

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
