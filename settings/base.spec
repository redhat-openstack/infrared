---
include_groups: ["Debug Options"]

shared_groups:
    - title: Debug Options
      options:
          debug:
              help: Run InfraRed in DEBUG mode
              short: d
              action: store_true
              nested: no

          # todo(obaranov) adding verbose here to pass gates
          # this should be removed prior merging the patch
          verbose:
              help: Control Ansible verbosity level
              short: v
              action: count
              default: 0

    - title: Ansible options
      options:
          verbose:
              help: Control Ansible verbosity level
              short: v
              action: count
              default: 0
          ansible-args:
            help: |
                Extra variables for ansible-playbook tool
                Should be specified as a list of ansible-playbook options, separated with commas.
                For example, --ansible-args="tags=overcloud,forks=500"
            type: AdditionalArgs

    - title: Inventory options
      options:
          inventory:
              help: Inventory file
              type: str
              default: local_hosts

    - title: Inventory hosts options
      options:
          inventory:
              help: Inventory file
              type: str
              default: hosts

    - title: Common options
      options:
          dry-run:
              action: store_true
              help: Only generate settings, skip the playbook execution stage
          input:
              action: append
              type: str
              short: i
              help: Input settings file to be loaded before the merging of user args
          output:
              type: str
              short: o
              help: 'File to dump the generated settings into (default: stdout)'
          extra-vars:
              action: append
              short: e
              help: Extra variables to be merged last
              type: str

    - title: Configuration file options
      options:
          from-file:
              action: read-config
              help: reads arguments from file.
          generate-conf-file:
              action: generate-config
              help: generate configuration file with default values
