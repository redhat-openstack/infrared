---
plugin_type: install
description: Check overcloud containers sanity 
subparsers:
    containers-sanity:
        help: Checks overcloud containers sanity
        include_groups: ['Ansible options', 'Inventory', 'Common options', 'Answers file']
        groups:
            - title: check overcloud containers sanity
              options:
                  host-ip:
                      type: Value
                      help: 'ip of the machine that containers sanity is tested on'
                      required: False 
                  host-username:
                      type: Value
                      help: 'username to ssh to the machine that containers sanity is tested on'
                      required: False
                  host-key_file:
                      type: Value
                      help: 'SSH key for the user <username>'
                      required: False
