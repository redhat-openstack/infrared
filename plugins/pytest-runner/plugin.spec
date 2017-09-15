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
                      type: Value
                      help: |
                          Location of the test file in the git repo.
                      default: 'tripleo/container_sanity.py'
