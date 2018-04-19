---
config:
    plugin_type: provision
subparsers:
    foreman:
        description: Provision systems using Foreman
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
                      help: 'User to Foreman server'
                      required: True
                  password:
                      type: Value
                      help: 'Password of Forman server'
                      required: True
                  strategy:
                      type: Value
                      help: 'Whether to use Foreman or system ipmi command.'
                      choices: ['foreman', 'ipmi']
                      default: foreman
                  action:
                      type: Value
                      help: 'Which command to send with the power-management selected by mgmt_strategy. For example - reset, reboot, cycle'
                      default: cycle
                  wait:
                      type: Value
                      default: 10
                      help: 'Number of seconds to wait before checking connectivity to the host after rebuild'


            - title: Host details
              options:
                  host-address:
                      type: Value
                      help: 'Name or ID of the host as listed in foreman'
                      required: yes
                  host-port:
                      type: Value
                      help: "Server's ssh port"
                      default: 22
                  host-user:
                      type: Value
                      help: 'User to SSH to the host with'
                      default: root
                  host-password:
                      type: Value
                      help: "User's SSH password"
                  host-key:
                      type: FileValue
                      help: "User's SSH key"
                  host-ipmi-address:
                      type: Value
                      help: "Host IPMI address"
                  host-ipmi-username:
                      type: Value
                      help: "Host IPMI username"
                  host-ipmi-password:
                      type: Value
                      help: "Host IPMI password"
                  os-id:
                      type: Value
                      help: "Operating system ID to set"
                  medium-id:
                      type: Value
                      help: "Medium ID to set"
                  ping-deadline:
                      type: Value
                      help: "Deadline in seconds for 'ping' command (If 'wait' isn't 0/False)"

            - title: Host roles
              options:
                  roles:
                      type: ListValue
                      help: |
                          Comma separated list of roles to apply to host.
                          For example - baremetal,undercloud,tester
                          Possible values: baremetal, undercloud, tester, hypervisor
                      default: baremetal
