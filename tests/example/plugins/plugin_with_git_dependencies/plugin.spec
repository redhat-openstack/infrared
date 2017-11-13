config:
   plugin_type: supported_type1
   dependencies:
      - source: "https://sample_github.null/plugin_repo.git"
        revision: "c5e3b060e8c4095c66db48586817db1eb02da338"
subparsers:
    plugin_with_dependencies:
        description: plugin1 of type1
        include_groups: []
