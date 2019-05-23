---
plugin_type: test
subparsers:
    pytest-runner:
        description: Pytest runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Test Control
              options:
                  run:
                      type: Bool
                      help: |
                          Whether to run the test or only to prepare for it.
                      default: True

                  repo:
                      type: Value
                      help: |
                          Git repo which contain the test.
                      default: 'https://code.engineering.redhat.com/gerrit/rhos-qe-core-installer'

                  file:
                      type: ListValue
                      help: |
                          Comma separated list of test files locations in git repo. Example:
                          'tripleo/container_sanity.py', 'tripleo/container_sanity_v3.py'
                      default: 'tripleo/container_sanity.py'
