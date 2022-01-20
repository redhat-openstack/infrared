plugin_type: test
subparsers:
    rally:
        description: Rally tests runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Common variables", "Answers file"]
        groups:
            - title: Rally
              options:
                  results-dir:
                      type: Value
                      help: |
                        Directory to store all the generated test results.
                        The directory location is on the Ansible control node,
                        and not on the Ansible Manage node/host that the test plugin is running on.
                      default: '{{ inventory_dir }}/test_results'
                  openstackrc:
                      type: Value
                      help: |
                          The full path or relative path to the openstackrc file.
                          When empty, infrared will search active profile for the 'keystonerc' file and use it.
                  git-repo:
                      type: Value
                      help: URL of the git repository to clone.
                      default: https://git.openstack.org/openstack/rally
                  git-revision:
                      type: Value
                      help: Revision of rally repository
                      default: HEAD
                  git-plugins-repo:
                      type: Value
                      help: URL of the plugins git repository to clone
                      required: no
                  git-plugins-revision:
                      type: Value
                      help: Revision of Rally plugins git repository
                      default: HEAD
                  setup:
                      type: Value
                      help: |
                          The setup type for rally.
                          __LISTYAMLS__
                      default: pip
                  tests:
                      type: VarFile
                      help: |
                          The set of tests to execute
                          __LISTYAMLS__
                      default: none.yml
                  tester-node:
                      type: Value
                      help: The name of the node from where to run the tests
                  image:
                      type: VarFile
                      help: |
                          The guest image to upload.
                          __LISTYAMLS__
                      default: cirros
                  deployment:
                      type: Value
                      help: The deployment name to use
                      default: cloud_under_test
                  taskfile:
                      type: Value
                      help: The task file to use
                      default: rally-jobs/mytest.json
                  delete-existing-venv:
                      type: Bool
                      help: |
                          Delete existing Rally virtual environment
                          (Shouldn't be used if Rally is installed from 'RPM')
                      default: True
