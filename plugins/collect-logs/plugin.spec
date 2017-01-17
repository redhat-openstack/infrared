# FIXME(aopincar): This plugin should be in a type of its own
plugin_type: install
description: Collect log from all nodes in the active profile.
subparsers:
    collect-logs:
        help: Collect log from all nodes in the active profile.
        include_groups: ["Ansible options", "Common options"]
        options:
          dest-dir:
              type: Value
              help: Path to a destination directory where the collected log will be stored
          gzip:
              type: Bool
              help: |
                  Whether using gzip to archive or not
                  When used - output files will be suffixed with ".gz"
              default: False
