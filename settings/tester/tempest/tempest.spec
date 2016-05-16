---
subparsers:
    tempest:
        include_groups: ['Ansible options', 'Inventory hosts options', 'Common options', 'Configuration file options']
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
                      type: YamlFile
                      help: The set of test to execute
                      required: yes
                      default: none.yml
                  threads:
                      type: Value
                      help: The number of concurrent threads to run tests
                      default: 8
