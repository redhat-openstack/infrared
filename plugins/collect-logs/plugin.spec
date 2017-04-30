# FIXME(aopincar): This plugin should be in a type of its own
plugin_type: other
subparsers:
    collect-logs:
        description: Collect log from all nodes in the active workspace.
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
