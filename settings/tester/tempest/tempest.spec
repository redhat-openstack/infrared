---
subparsers:
    tempest:
        include_groups: ['Ansible options', 'Inventory hosts options', 'Common options', 'Configuration file options']
        help: Tempest tests runner
        groups:
            - title: Tempest
              options:
                  setup:
                      type: YamlFile
                      help: The setup type for tests
                      required: yes
                      default: git.yml
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
                          By default the inventory_dir/keystonerc file will be used.
                  openstack-version:
                       type: Value
                       help: |
                           The Openstack under test version.
                           This value can be overridden by the extra vars: '-e installer.product.version=<value>'
                       choices: ['5', '6', '7', '8', '9', '10']
                  openstack-installer:
                       type: Value
                       help: |
                           The Openstack installation type.
                           This value can be overridden by the extra vars: '-e installer.type=<value>'.
                       choices: ['packstack', 'ospd']
                  config-options:
                       type: DictValue
                       help: |
                           Forces additional Tempest configuration (tempest.conf) options.
                           Format: --config-options="section.option=value1;section.option=value".
                  setup-revision:
                      type: Value
                      help: The setup (git) revision if applicable
                      default: HEAD
                  tests:
                      type: ListOfYamls
                      help: |
                        The set of tests to execute. Should be specified as list
                        constructed from the allowed values.
                        For example: smoke,network,volumes
                      required: yes
                  threads:
                      type: Value
                      help: The number of concurrent threads to run tests
                      default: 8
                  base-image:
                      type: Value
                      help: Unified image to be used for Tempest
                      default: http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img
