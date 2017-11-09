---
config:
    plugin_type: test
    dependencies:
        - source: ./.library/common
subparsers:
    tempest:
        description: The tempest test runner
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
                           The OpenStack under test version.
                           Numbers are for OSP releases
                           Names are for RDO releases
                       choices:
                           - "6"
                           - "7"
                           - "8"
                           - "9"
                           - "10"
                           - "11"
                           - "12"
                           - liberty
                           - kilo
                           - liberty
                           - mitaka
                           - newton
                           - ocata
                           - pike
                           - queens
                  openstack-installer:
                       type: Value
                       help: |
                           The OpenStack installation type.
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
                  image:
                      type: Value
                      help: |
                          An image to be uploaded to glance and used for testing. Path have to be a url.
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
                  blackre:
                      type: Value
                      help: |
                          Adds an extra black (skip) regex to the ostestr/tempest invocation.
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
                  python_tempest_conf_dir:
                      type: Value
                      help: |
                          The full or relative path to the python-tempestconf destination.
                          Suitable when setup is 'git'. When the path is specified, python-tempestconf is not cloned
                          from the repository but the code in a location specified by the path is used instead.
                  results-formats:
                      type: Value
                      help: |
                          Output format of tempest results report to generate. Currently supported: junitxml, html.
                          Format: --results-formats junitxml,html
                      default: junitxml
