subparsers:
    rally:
        formatter_class: RawTextHelpFormatter
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
                      help: The set of test to execute
                      required: yes
                      default: none.yml
            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook execution stage
                  cleanup:
                      action: store_true
                      help: Clean given system instead of provisioning a new one
                  input:
                      action: append
                      type: str
                      short: i
                      help: Input settings file to be loaded before the merging of user args
                  output:
                      type: str
                      short: o
                      help: 'File to dump the generated settings into (default: stdout)'
                  extra-vars:
                      action: append
                      short: e
                      help: Extra variables to be merged last
                      type: str
                  from-file:
                      type: IniFile
                      help: the ini file with the list of arguments
                  generate-conf-file:
                      type: str
                      help: generate configuration file (ini) containing default values and exits. This file is than can be used with the from-file argument
