---
config:
    plugin_type: test
subparsers:
    tempest:
        description: The tempest test runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Common variables", "Answers file"]
        groups:
            - title: Tempest
              options:
                  results-dir:
                      type: Value
                      help: |
                        Directory to store all the generated test results.
                        The directory location is on the Ansible control node,
                        and not on the Ansible Manage node/host that the test plugin is running on.
                  tempest-config:
                      type: Bool
                      help: |
                          Create tempest configuration file
                      default: yes
                  tests:
                      type: ListOfVarFiles
                      help: |
                        The set of tests to execute. Should be specified as list
                        constructed from the allowed values.
                        For example: smoke,network,volumes
                        __LISTYAMLS__
                      required: yes
                  mode:
                      type: Value
                      help: |
                        Mode tempest plugin should run in.
                        normal - use RPM version of Tempest (the usual way Tempest is ran)
                        debug_failing - installs tempest patches with highly experimental
                            features (i.e.: run_on_failure) that are not yet merged to
                            main Tempest project. See https://review.opendev.org/#/c/553896/
                            for more details.
                            Tested only on OSP12 and above.
                        debug_all - an extended version of 'debug_failing' but running
                            debugging/info capturing commands on _all_ tempest tests.
                            Useful when troubleshooting resource leaks and other problems
                            not directly related to tempest tests failures.
                            Use with caution (i.e.: only with small test suites) as it consumes
                            build time and disk space considerably.
                        NOTE: See 'debug-command' below.
                      choices:
                        - normal
                        - debug_failing
                        - debug_all
                      default: normal
                  tester-node:
                      type: Value
                      help: |
                        The name of the node from where to run the tests.
                        NOTE: this param is ignored if --openstack-installer is 'packstack' because Ansible inventory
                        already has a tester node added by 'openstack' Infrared plugin (and it's not in undercloud group).
                  debug-command:
                      type: Value
                      help: |
                        Value of this parameter takes effect only when --mode is 'debug_failing'
                        or 'debug_all'. Command given here will be run by tempest on each test's
                        teardown phase (before resources used by that test are torn down).
                        The command can be any command available on the 'tester' node (the one tempest
                        runs on) or a URL to an shell executable file (it will be downloaded
                        and executed).
                        Examples:
                            --debug-command 'ovs-vsctl show br-int'
                            --debug-command 'http://someurl/my_debug_script.sh'
                      default: 'sosreport --batch --build --tmp-dir /var/log/extra --log-size=1 -p openstack'
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
                        Optionally, a refspec can be provided, separated by comma too.
                        If version is set to a SHA-1 not reachable from any branch or tag,
                        refspec option may be necessary to specify the ref containing the SHA-1.
                            --plugin=repo_url,version,refspec
                        More than one --plugin option can be provided.
                        Examples:
                            --plugin 'https://<code_repo1>'
                            --plugin 'https://<code_repo2>,<sha-1|branch|tag>'
                            --plugin 'https://<code_repo3>,<sha-1|branch|tag|FETCH_HEAD>,refs/changes/xx/yyyyyy/zz'
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
                           - "15"
                           - "15-trunk"
                           - "16"
                           - "16-trunk"
                           - "16.1"
                           - "16.1-trunk"
                           - "16.2"
                           - "16.2-trunk"
                           - "17"
                           - "17.0"
                           - "17.1"
                           - "17-trunk"
                           - liberty
                           - kilo
                           - liberty
                           - mitaka
                           - newton
                           - ocata
                           - pike
                           - queens
                           - rocky
                           - stein
                           - train
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
                  images-command:
                      type: Value
                      help: |
                          A command to execute inside tempest guest image.
                          This option requires 'image' option to be specified and will fail without it.
                  config-longopt:
                       action: append
                       help: |
                           Extra long argument without the leading '--' passed to python-tempestconf.
                           Format: --config-longopt image-disk-format=raw
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
                  component_threads:
                      type: NestedDict
                      help: |
                          Used to set the number of threads for suite test
                          Format: --component_threads manila_scenario=1,cinder=4
                  revision:
                      type: Value
                      help: The setup (git) revision if applicable
                  gerrit_review:
                      type: Value
                      help: |
                          Cherry-pick the given change from Gerrit. Only applicable to the git installation method.
                  threads:
                      type: Value
                      help: The number of concurrent threads to run tests
                      default: 8
                  dir:
                      type: Value
                      help: The tempest working directory on the tester node
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
                      default: junitxml,html
                  test-suite-prefix:
                      type: Value
                      help: Prefix for test suite name to be specified in junitxml report file.
                      default: ''
                  test-step-id:
                      type: Value
                      help: |
                          Step identifier to be appended to each output file.
                          If not specified, an auto-incremental number is used starting from 1.
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
                  configure-whitebox-plugin:
                      type: Bool
                      help: |
                          This configures "[whitebox]\nhypervisors" field in tempest.conf based on Whitebox Tempest Plugin.
                          A list of mapped hypervisors with their external IP are configured automatically based on the deployment.
                          Ex- hypervisors=compute-0.localdomain:192.168.24.5,compute-1.localdomain:192.168.24.11
                          Plugin url: https://review.rdoproject.org/r/openstack/whitebox-tempest-plugin
                          NOTE: vars/tests/whitebox_plugin.yml need to be included to execute Whitebox tests
                      default: no
                  configure-whitebox-db:
                      type: Bool
                      help: |
                          Configures following fields in [whitebox-database] section in tempest.conf:
                          internal_ip (Controller), host (Controller), password (NovaPassword) useful for connections to Nova database
                      default: no
                  sdir:
                      type: Value
                      help: |
                          A path to a custom stestr dir containing timing data. The custom-stestr-dir will be copied to dir location.
                          NOTE: the path must end with a trailing slash (/)
                  customized-image-flavor:
                      type: Bool
                      help: |
                          Configures ids of customized images and flavors created in cloud-config 'create_flavors_image' task
                          Plugin url: https://github.com/rhos-infra/cloud-config
                          NOTE: 'customized_flavor', 'customized_flavor_alt', <hostname-url>, <hostname-url>_alt should
                          be pre-created, preferably by the 'create_flavors_image' task before using this option 
                          NOTE: <hostname-url> is the basename of the image used. Both tempest image and cloud-config image specs should
                          be defined the same. Example- 'cirros-0.5.2-x86_64-disk.img' would be the name of the image when the following
                          image spec is passed:  https://download.cirros-cloud.net/0.5.2/cirros-0.5.2-x86_64-disk.img
                      default: no
                  rpm-package:
                      type: Value
                      help: A URL of tempest RPM package to be installed from external source.
                      default: ''
                  install-crudini:
                      type: Bool
                      help: Install crudini on all controller nodes (required by some tests).
                      default: no
            - title: ansible facts
              options:
                  collect-ansible-facts:
                      type: Bool
                      help: Save ansible facts as json file(s)
                      default: False
