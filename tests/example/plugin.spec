plugin_type: provision
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

                  dictionary-val:
                      type: KeyValueList
                      help: "dictionary-val option"

            - title: Group B
              options:
                  iniopt:
                      type: IniType
                      help: "Help for '--iniopt'"
                      action: append

            - title: Group C
              options:
                  uni-dep:
                      type: Value
                      help: "Help for --uni-dep"
                      required_when: "req-arg-a == yes"

                  multi-dep:
                      type: Value
                      help: "Help for --multi-dep"
                      required_when:
                          - "req-arg-a == yes"
                          - "req-arg-b == yes"

                  req-arg-a:
                      type: Bool
                      help: "Help for --req-arg-a"

                  req-arg-b:
                      type: Bool
                      help: "Help for --req-arg-b"
