plugin_type: supported_type1
subparsers:
    unsupported_spec_option_type:
        description: A description for plugin with unsupported option in spec
        include_groups: []
        groups:
            - title: AGroup
              options:
                  some-option:
                      type: UnsupportedType
                      help: 'some-option help'
