plugin_type: test
description: The tempest test runner
subparsers:
    tempest:
        help: The tempest test runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Tempest
              options:
                  tests:
                      type: ListValue
                      help: |
                        The set of tests to execute. Should be specified as list
                        constructed from the allowed values.
                        For example: smoke,network,volumes
                        __LISTYAMLS__
                      required: yes
                  openstack-version:
                       type: Value
                       help: |
                           The Openstack under test version.
                       choices: ['5', '6', '7', '8', '9', '10', '11']
                       required: yes
                  openstack-installer:
                       type: Value
                       help: |
                           The Openstack installation type.
                       choices:
                           - packstack
                           - tripleo
                       required: yes
                  setup:
                      type: Value
                      help: |
                          The setup type for tests
                          __LISTYAMLS__
                      default: git
                  deployer-input-method:
                      type: Value
                      help: |
                          Possible values:
                             - copy: The deployer-input specified by the '--deployer-input-file' argument will be copied from the host station.
                             - local: The deployer-input file to use from the tester folder on tester station.
                      choices: [copy, local]
                      default: copy
                  deployer-input-file:
                      type: Value
                      help: |
                          Required when the 'deployer-input-method' option is set.
                          Specifies the deployer-input file location. When  deployer-input-method == 'copy' the absolute path to the file should be specified.
                          When  deployer-input-method == 'local' the tempest-dir relative path should be specified (e.g. etc/deployer-config-icehouse.conf).
                  openstackrc:
                      type: Value
                      help: |
                          The full path to the openstackrc file.
                          When empty, will search active profile for 'keystonerc' file"
                  config-options:
                       type: KeyValueList
                       help: |
                           Forces additional Tempest configuration (tempest.conf) options.
                           Format: --config-options="section.option:value1,section.option:value".
                  revision:
                      type: Value
                      help: The setup (git) revision if applicable
                      default: HEAD
                  threads:
                      type: Value
                      help: The number of concurrent threads to run tests
                      default: 8
                  dir:
                      type: Value
                      help: The tempest wokring direcotry on the tester node
                      default: tempest-dir
