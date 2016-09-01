subparsers:
    integration:
        include_groups: ['Ansible options', 'Inventory hosts options', 'Common options', 'Configuration file options']
        help: Integration tests runner
        groups:
            - title: Component selection
              options:
                  component:
                      type: YamlFile
                      help: Name of test component
                      default: horizon.yml
            - title: Horizon
              options:
                  git-repo:
                      type: YamlFile
                      help: The setup (git) revision if applicable
                      default: horizon-integration-tests.yml
                  git-revision:
                      type: Value
                      help: Git refspec (mostly branch) in test repository
                      default: HEAD
                  horizon-tests:
                      type: Value
                      choices: ['all']
                      help: The set of test to execute
                      default: all
                  horizon-selenium-grid:
                      type: Value
                      choices: ['local', 'sauce']
                      help: Specify which selenium grid service should be used
                      default: local
