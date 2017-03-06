plugin_type: test
description: The gabbi test runner
subparsers:
    gabbi:
        help: The gabbi test runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Gabbi
              options:
                  openstack-version:
                       type: Value
                       help: |
                           The Openstack under test version.
                       choices: ['5', '6', '7', '8', '9', '10', '11']
                       required: yes
                  network:
                       type: Value
                       help: |
                         The network settings to use
                         __LISTYAMLS__
                       default: default_ipv4
                  openstackrc:
                      type: Value
                      help: |
                          The full path or relative path to the openstackrc file.
                          When empty, infrared will search active workspace for the 'keystonerc' file and use it.
                  undercloudrc:
                      type: Value
                      help: |
                          The full path or relative path to the undercloudrc file.
                          When empty, infrared will search active workspace for the 'stackrc' file and use it.
                  setup:
                      type: Value
                      help: |
                          The setup parameters
                          __LISTYAMLS__
                      default: default
