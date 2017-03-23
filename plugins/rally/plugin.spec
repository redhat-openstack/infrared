plugin_type: test
description: Rally tests runner
subparsers:
    rally:
        help: Rally tests runner
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Rally
              options:
                  openstackrc:
                      type: Value
                      help: |
                          The full path or relative path to the openstackrc file.
                          When empty, infrared will search active profile for the 'keystonerc' file and use it.
                  git-repo:
                      type: Value
                      help: URL of the git repository to clone
                      default: https://git.openstack.org/openstack/rally
                  git-revision:
                      type: Value
                      help: Revision of rally repository
                      default: HEAD
                  tests:
                      type: VarFile
                      help: |
                          The set of tests to execute
                          __LISTYAMLS__
                      required: no
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
