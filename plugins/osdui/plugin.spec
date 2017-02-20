plugin_type: test
description: The ospdui test runner
subparsers:
    ospdui:
        help: The ospdui test runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Setup
              options:
                  openstack-version:
                      type: Value
                      help: |
                          The Openstack under test version.
                      choices: ['10', '11']
                      required: yes
                  tests:
                      type: Value
                      help:
                           The test suite to run. This value will be passed to the test runner.
                           __LISTYAMLS__
                      required: yes
                  ssl:
                      type: Value
                      help: specifies whether the ui should be accessed by https for http protocol.
                      default: no
                  setup:
                      type: Value
                      help: |
                          The ospdui setup parameters
                          __LISTYAMLS__
                      default: default
                  webdriver:
                      type: Value
                      help: The web driver to use
                      choices:
                          - firefox
                          - chrome
                          - marionette
                      default: firefox
                  environment-url:
                      type: Value
                      help: |
                          The link where the environment files for the sepcific baremetal environment (especially instackenv.json) can be found
                      default: ''
                  config:
                      type: Value
                      help: |
                          The test framework configuration file to use instead of the default.
