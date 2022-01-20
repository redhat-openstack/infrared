---
config:
    plugin_type: test
subparsers:
    ospdui:
        description: The ospdui test runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Common variables", "Answers file"]
        groups:
            - title: Setup
              options:
                  results-dir:
                      type: Value
                      help: Directory to store all the generated test results
                      default: '{{ inventory_dir }}/test_results'
                  openstack-version:
                      type: Value
                      help: |
                          The OpenStack under test version.
                      choices: ['10', '11', '12', '13', '14']
                      required: yes
                  undercloudrc:
                      type: Value
                      help: |
                          The full path or relative path to the undercloud rc file.
                          When empty, infrared will search active workspace for the 'stackrc' file and use it.
                  tests:
                      type: Value
                      help:
                           The full path or relative path to tests to run. This value will be passed to the test runner.
                      required: yes
                  ssl:
                      type: Bool
                      help: specifies whether the ui should be accessed by https for http protocol.
                      default: no
                  setup:
                      type: VarFile
                      help: |
                          The ospdui setup parameters
                          __LISTYAMLS__
                      default: default
                  browser:
                      type: Value
                      help: The web broser to use
                      choices:
                          - firefox
                          - chrome
                          - marionette
                      default: firefox
                  environment-url:
                      type: Value
                      help: |
                          The link where the environment files for the specific baremetal environment (especially instackenv.json) can be found
                      default: ''
                  plan:
                      type: Value
                      help: The test plan file name to use for tests.
                      default: plan.tgz
                  config:
                      type: Value
                      help: |
                          The test framework configuration file to use instead of the default.
                  topology-config:
                      type: VarFile
                      help: |
                          The topology configuration to be used.
                      default: default.conf
