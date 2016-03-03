---
options:
    verbose:
        help: 'Verbosity level'
        short: v
        action: count
        default: 0
    inventory:
        help: 'Inventory file'
        short: i
        type: str
        default: local_hosts
    debug:
        help: 'Set log level to DEBUG'
        short: d
        action: store_true
