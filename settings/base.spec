---
groups:
    - name: Debug Options
      options:
          - name: debug
            help: 'Run InfraRed in DEBUG mode'
            short: d
            action: store_true
            nested: no
          # todo(obaranov) adding verbose here to pass gates
          # this should be removed prior merging the patch
          - name: verbose
            help: 'Control Ansible verbosity level'
            short: v
            action: count
            default: 0
            nested: no

    - name: Ansible options
      options:
          - name: verbose
            help: 'Control Ansible verbosity level'
            short: v
            action: count
            default: 0
            nested: no

    - name: Inventory options
      options:
          - name: inventory
            help: 'Inventory file'
            type: str
            default: local_hosts
            nested: no

    - name: Common options
      options:
          - name: dry-run
            action: store_true
            help: Only generate settings, skip the playbook execution stage
            nested: no
          - name: input
            action: append
            type: str
            short: i
            help: Input settings file to be loaded before the merging of user args
            nested: no
          - name: output
            type: str
            short: o
            help: 'File to dump the generated settings into (default: stdout)'
            nested: no
          - name: extra-vars
            action: append
            short: e
            help: Extra variables to be merged last
            type: str
            nested: no

    - name: Configuration file options
      options:
          - name: from-file
            action: read-config
            help: reads arguments from file.
            nested: no
          - name: generate-conf-file
            action: generate-config
            help: generate configuration file with default values
            nested: no

