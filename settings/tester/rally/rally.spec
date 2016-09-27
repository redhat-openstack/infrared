subparsers:
    rally:
        include_groups: ['Ansible options', 'Inventory hosts options', 'Common options', 'Configuration file options']
        help: Rally tests runner
        groups:
            - title: Rally
              options:
                  git-repo:
                      type: Value
                      help: URL of the git repository to clone
                      default: https://git.openstack.org/openstack/rally
                  git-revision:
                      type: Value
                      help: Revision of rally repository
                      default: HEAD
                  git-plugins-repo:
                      type: Value
                      help: URL of the plugins git repository to clone
                      default: https://github.com/redhat-openstack/rally-plugins.git
                  git-plugins-revision:
                      type: Value
                      help: Revision of plugins repository
                      default: HEAD
                  tests:
                      type: YamlFile
                      help: The set of tests to execute (optional, but provide tester.rally.taskdir and tester.rally.taskfile, which when concatenated point to the task you want to run)
                      required: no

