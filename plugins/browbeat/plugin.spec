config:
    plugin_type: test
subparsers:
    tempest:
        description: The Browbeat performance test runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Browbeat
              options:
                  config-file:
                      type: FileValue
                      help: |
                        The browbeat configuration to execute
                  workloads:
                      type: Value
                      nargs: '*'
                      help: |
                        The workloads to run 
       __         
