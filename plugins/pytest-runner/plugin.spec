---
plugin_type: test
subparsers:
    pytest-runner:
        description: Pytest runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Test Control
              options:
                  results-dir:
                      type: Value
                      help: |
                        Directory to store all the generated test results.
                        The directory location is on the Ansible control node,
                        and not on the Ansible Manage node/host that the test plugin is running on.
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

                  tester-node:
                      type: Value
                      help: The name of the node from where to run the tests