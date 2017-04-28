plugin_type: install
description: Overcloud auto configuration of fencing
subparsers:
    tripleo-fencing:
        help: Overcloud auto-fencing
        include_groups: ["Ansible options", "Common options"]
        groups:
            - title: Deployment Description
              options:
                  version:
                      type: Value
                      required: True
                      help: |
                          The product version (product == director)
                          Numbers are for OSP releases
                          Names are for RDO releases
                      choices:
                        - "7"
                        - "8"
                        - "9"
                        - "10"
                        - "11"
                        - "12"
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                        - pike
