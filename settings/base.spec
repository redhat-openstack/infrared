---
groups:
    - name: Logging arguments
      options:
          - name: verbose
            help: 'Control Ansible verbosity level'
            short: v
            action: count
            default: 0
          - name: debug
            help: 'Run InfraRed in DEBUG mode'
            short: d
            action: store_true

    - name: Inventory arguments
      options:
          - name: inventory
            help: 'Inventory file'
            type: str
            default: local_hosts

    - name: Common arguments
      options:
          - name: dry-run
            action: store_true
            help: Only generate settings, skip the playbook execution stage
          - name: cleanup
            action: store_true
            help: Clean given system instead of running playbooks on  a new one
          - name: input
            action: append
            type: str
            short: i
            help: Input settings file to be loaded before the merging of user args
          - name: output
            type: str
            short: o
            help: 'File to dump the generated settings into (default: stdout)'
          - name: extra-vars
            action: append
            short: e
            help: Extra variables to be merged last
            type: str

    - name: Configuration file arguments
      options:
          - name: from-file
            action: read-config
            help: reads arguments from file.
          - name: generate-conf-file
            action: generate-config
            help: generate configuration file with default values

