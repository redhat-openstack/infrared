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
                      type: ListOfVarFiles
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
                          The setup type for tests and for the tempestconf tool.
                          __LISTYAMLS__
                      default: rpm
                  deployer-input-file:
                      type: Value
                      help: |
                          The deployer input file absolute or relative path.
                          By default will try to use the 'deployer-input-file.conf' file from active workspace folder.
                  openstackrc:
                      type: Value
                      help: |
                          The full path or relative path to the openstackrc file.
                          When empty, infrared will search active workspace for the 'keystonerc' file and use it.
                  config-options:
                       type: IniType
                       action: append
                       help: |
                           Forces additional Tempest configuration (tempest.conf) options.
                           Format: --config-options section.option:value1 --config-options section.option:value
                  remove-options:
                       type: IniType
                       action: append
                       help: |
                           Remove additional Tempest configuration (tempest.conf) options.
                           Format: --remove-options section.option:value1 --remove-options section.option:value
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
                  legacy-config:
                      type: Bool
                      help: |
                          Specifies whether the tempest configuration should use legacy method by running configuration
                          from the tempest repo itself without using the tempestconf package. Suitable only when
                          setup is 'git'
                      default: no
                  cleanup:
                      type: Bool
                      help: |
                          Use tempest cleanup to clean the leftover from the tests (usually when tests fail)
                      default: no
