config:
   plugin_type: provision
   entry_point: main.yml
   dependencies:
      - source: "https://sample_github.null/dependency_repo.git"
        revision: "c5e3b060e8c4095c66db48586817db1eb02da338"
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

            - title: Group D
              options:
                    deprecated-way:
                        type: Value
                        help: "Deprecated way to do it"
                    new-way:
                        deprecates: deprecated-way
                        type: Value
                        help: "New way to do it"

            - title: Group E
              options:
                    tasks:
                        type: ListOfFileNames
                        help: |
                            This is example for option which is with type "ListOfFileNames" and has
                            auto propagation of "Allowed Values" in help. When we ask for --help it
                            will look in plugin folder for directory name as 'lookup_dir' value, and
                            will add all file names to "Allowed Values"
                        lookup_dir: 'post_tasks'