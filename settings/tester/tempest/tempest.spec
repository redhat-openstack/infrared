subparsers:
    tempest:
        formatter_class: RawTextHelpFormatter
        help: Tempest tests runner
        groups:
            - title: Tempest
              options:
                  setup:
                      type: YamlFile
                      help: The setup type for tests
                      required: yes
                      default: git.yml
                  setup-revision:
                      type: Value
                      help: The setup (git) revision if applicable
                      default: HEAD
                  tests:
                      type: ListOfYamls
                      help: |
                        The set of tests to execute. Should be specified as list
                        constructed from the allowed values.
                        For example: smoke,network,volumes
                      required: yes
                  threads:
                      type: Value
                      help: The number of concurrent threads to run tests
                      default: 8
            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook execution stage
                  cleanup:
                      action: store_true
                      help: Clean given system instead of provisioning a new one
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
                  from-file:
                      type: IniFile
                      help: the ini file with the list of arguments
                  generate-conf-file:
                      type: str
                      help: generate configuration file (ini) containing default values and exits. This file is than can be used with the from-file argument
