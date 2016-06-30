subparsers:
    integration:
        formatter_class: RawTextHelpFormatter
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
                  setup:
                      type: YamlFile
                      help: The setup type for tests
                      default: git.yml
                  git-repo:
                      type: YamlFile
                      help: The setup (git) revision if applicable
                      default: horizon-integration-tests.yml
                  git-revision:
                      type: Value
                      help: Git refspec (mostly branch) in test repository
                      default: HEAD
                  tests:
                      type: YamlFile
                      help: The set of test to execute
                      default: all.yml
            - title: common
              options:
                  input:
                      action: append
                      type: str
                      short: i
                      help: Input settings file to be loaded before the merging of user args
                  output:
                      type: str
                      short: o
                      help: 'File to dump the generated settings into (default: stdout)'
