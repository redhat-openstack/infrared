---
options:
    verbose:
        help: 'Control Ansible verbosity level'
        short: v
        action: count
        default: 0
    inventory:
        help: 'Inventory file'
        type: str
        default: local_hosts
    debug:
        help: 'Run InfraRed in DEBUG mode'
        short: d
        action: store_true
