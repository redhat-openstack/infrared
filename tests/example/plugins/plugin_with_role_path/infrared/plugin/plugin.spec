config:
   plugin_type: supported_type1
   entry_point: 'main.yml'
   roles_path: ../../
subparsers:
    example:
        description: Example provisioner plugin
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Group A
              options:
                  foo-bar:
                      type: Value
                      help: "foo.bar option"
                      default: "default string"

                  flag:
                      type: Flag
                      help: "flag option"

                  dictionary-val:
                      type: KeyValueList
                      help: "dictionary-val option"
