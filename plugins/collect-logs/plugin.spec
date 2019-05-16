# FIXME(aopincar): This plugin should be in a type of its own
plugin_type: other
subparsers:
    collect-logs:
        description: Collect log from all nodes of the active workspace.
        include_groups: ["Ansible options", "Common options"]
        options:
          hosts:
              type: Value
              help: |
                  Inventory hosts or group to collect logs from. The ansbile host pattern can be used as a value.
                  (https://docs.ansible.com/ansible/devel/user_guide/intro_patterns.html).
                  To set that value from shell use single quotes or escape special characters. For example:
                      infrared collect-logs --hosts 'all:!localhost'
                      infrared collect-logs --hosts "overcloud_nodes:\!compute:\!localhost"

              default: "all:!localhost:!hypervisor"
          dest-dir:
              type: Value
              help: Path to a destination directory where the collected log will be stored
          archive-custom:
              type: Value
              help: Comma,separated list of additional path(s) to be archived.
          gzip:
              type: Bool
              help: |
                  Whether using gzip to archive or not
                  When used - output files will be suffixed with ".gz"
              default: False
          max-depth:
              type: Value
              help: Deprecated, does nothing, will be removed
              default: 4
          logger:
              type: Value
              help: |
                    Specifies which facility we are using for log collection:
                        * host - gather and fetch log files from the system
                        * sosreport - use sosreport utility to get logs
                        * all -  use both variants
              choices: ['host', 'sosreport', 'all']
              default: 'host'
