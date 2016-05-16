---
command:
    subcommands:
        - name: beaker
          help: Provision systems using Beaker
          include_groups: ['Logging arguments', 'Inventory arguments', 'Common arguments', 'Configuration file arguments']
          groups:
              - name: Beaker server
                options:
                    - name: base-url
                      help: Base URL of Beaker server
                      required: True
                    - name: username
                      help: 'Login username to authenticate to Beaker (default: __DEFAULT__)'
                      default: admin
                    - name: password
                      help: Password of login user
                      required: True
                    - name: web-service
                      help: Web service
                      default: 'rest'
                      choices: ['rest', 'rpc']
                    - name: ca-cert
                      help: CA Certificate
                      required: False
              - name: Beaker system
                options:
                    - name: fqdn
                      help: Fully qualified domain name of a system
                      required: True
                    - name: distro-tree
                      help: Distro Tree ID
                      default: 71576

              - name: Cleanup
                options:
                    - name: cleanup
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      nested: no
