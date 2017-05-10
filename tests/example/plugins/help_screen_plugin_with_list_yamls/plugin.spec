plugin_type: supported_type1
subparsers:
    list_yamls_plugin:
        description: Description for list_yamls_plugin
        groups:
            - title: AGroup
              options:
                  topology:
                      type: Value
                      help: |
                            help of topology option
                            __LISTYAMLS__

                  topology-networks:
                      type: Value
                      help: |
                            help of topology-networks option
                            __LISTYAMLS__
