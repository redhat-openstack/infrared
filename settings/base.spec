---
options:
    verbose:
        help: 'Control Ansible verbosity level'
        short: v
        action: count
        default: 0
    debug:
        help: 'Run InfraRed in DEBUG mode'
        short: d
        action: store_true
