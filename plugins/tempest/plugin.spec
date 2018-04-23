---
config:
    plugin_type: test
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
                  plugin:
                      type: Value
                      action: append
                      help: |
                        The list of additional plugins with tests to install.
                        Should be specified in the following format:
                            --plugin=repo_url
                        The plugin flag can also specify the version/branch to clone.
                        In order to specify version the repo_url should be separated by comma:
                            --plugin=repo_url,version
                        More than one --plugin option can be provided.
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
                           - "13"
                           - "14"
                           - liberty
                           - kilo
                           - liberty
                           - mitaka
                           - newton
                           - ocata
                           - pike
                           - queens
                           - rocky
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
                      type: FileValue
                      help: |
                          The deployer input file absolute or relative path.
                          By default will try to use the 'deployer-input-file.conf' file from active workspace folder.
                  openstackrc:
                      type: FileValue
                      help: |
                          The full path or relative path to the openstackrc file.
                          When empty, infrared will search active workspace for the 'keystonerc' file and use it.
                  image:
                      type: Value
                      help: |
                          An image to be uploaded to glance and used for testing. Path have to be a url.
                  images-packages:
                      type: Value
                      help: | 
                          Comma delimited list of packages to install in guest image tempest will use for testing.
                          This option requires 'image' option to be specified and will fail without it.
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
                          To add multiple tests seperate by pipe.
                  regexlist-file:
                      type: Value
                      help: |
                          A path to a file that contains a list of regular expressions with black/white-listed tests.
                          Black/white-listed tests will be ammended to the tempest black/white-list files.
                          Example of the regexlist-file content
                          blacklist: [
                              test.foo.1,
                              test.foo.2
                          ]
                          whitelist: [
                              test.zoo.1,
                              test.zoo.2
                          ]
                          foo.1, foo.2 will be ammended to the tempest blacklist file, while zoo.1, zoo.2 will
                          be ammended to the tempest whitelist file (in addition to the tests that were contained
                          therein). For more details on how black/white list operate refer to:
                          http://stestr.readthedocs.io/en/latest/MANUAL.html#test-selection
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
                  list:
                      type: Bool
                      help: List all the tests which will be run.
                      default: no
                  packages:
                      type: Value
                      help: Comma,delimited list of packages to install system-wide before installing tests packages and their requirements.
                  pip-packages:
                      type: Value
                      help: Comma,delimited list of pip packages to install system-wide before installing tests packages and their requirements.
                  post-config-commands:
                      type: ListValue
                      help: |
                          Comma separated list of commands to execute after tempest config is executed.
                          For example: 'ls -l','echo awesome'
            - title: ansible facts
              options:
                  collect-ansible-facts:
                      type: Bool
                      help: Save ansible facts as json file(s)
                      default: False
