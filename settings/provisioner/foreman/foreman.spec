---
command:
    subcommands:
        - name: foreman
          help: Provision systems using Foreman
          include_groups: ['Ansible options', 'Inventory options', 'Common options', 'Configuration file options']
          groups:
              - name: foreman
                options:
                    - name: user
                      help: User to Forman server
                      required: True
                    - name: password
                      help: Password of Forman server
                      required: True
                    - name: url
                      help: The Foreman api url
                      required: True
                    - name: strategy
                      help: Whether to use Foreman or system ipmi command.
                      default: foreman
                    - name: action
                      help: Which command to send with the power-management selected by mgmt_strategy. For example - reset, reboot, cycle
                      default: cycle
                    - name: wait
                      default: true
                      help: Whether we should wait for the host given the 'rebuild' state was set.
              - name: host
                options:
                    - name: host-address
                      help: Name or ID of the host as listed in foreman
                      required: yes
                    - name: host-key
                      help: "User's SSH key"
                      default: ~/.ssh/id_rsa

              - name: Cleanup
                options:
                    - name: cleanup
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      nested: no
