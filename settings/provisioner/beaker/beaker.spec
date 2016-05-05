---
subparsers:
    beaker:
        help: Provision systems using Beaker
        groups:
            - title: Beaker server
              options:
                  base-url:
                      type: Value
                      help: Base URL of Beaker server
                      required: True
                  username:
                      type: Value
                      help: 'Login username to authenticate to Beaker (default: __DEFAULT__)'
                      default: admin
                  password:
                      type: Value
                      help: Password of login user
                      required: True
                  web-service:
                      type: Value
                      help: Web service
                      default: 'rest'
                      choices: ['rest', 'rpc']
                  ca-cert:
                      type: Value
                      help: CA Certificate
                      required: False
            - title: Beaker system
              options:
                  fqdn:
                      type: Value
                      help: Fully qualified domain name of a system
                      required: True
                  distro-tree:
                      type: Value
                      help: Distro Tree ID
                      default: 71576
            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook execution stage
                  cleanup:
                      action: store_true
                      help: Release the system
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
