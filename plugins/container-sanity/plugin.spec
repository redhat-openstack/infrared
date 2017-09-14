---
plugin_type: test
subparsers:
    container-sanity:
        description: Container sanity test
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Test Control
              options:
                  run:
                      type: Bool
                      help: |
                          Whether it run the test or only to prepare them.
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
