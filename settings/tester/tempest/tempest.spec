command:
    subcommands:
        - name: tempest
          include_groups: ['Logging arguments', 'Inventory arguments', 'Common arguments', 'Configuration file arguments']
          help: Tempest tests runner
          groups:
            - name: Tempest
              options:
                    - name: setup
                      complex_type: YamlFile
                      help: The setup type for tests
                      required: yes
                      default: git.yml
                    - name: setup-revision
                      help: The setup (git) revision if applicable
                      default: HEAD
                    - name: tests
                      complex_type: YamlFile
                      help: The set of test to execute
                      required: yes
                      default: none.yml
                    - name: threads
                      help: The number of concurrent threads to run tests
                      default: 8
            - name: Cleanup
              options:
                  - name: cleanup
                    action: store_true
                    help: Clean given system instead of running playbooks on a new one.
                    nested: no
