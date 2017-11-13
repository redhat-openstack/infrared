config:
   plugin_type: supported_type1
   dependencies:
      - source: tests/example/plugins/plugin_with_dependencies/plugin_dependency
subparsers:
    plugin_with_dependencies:
        description: plugin1 of type1
        include_groups: []
