---
plugin_type: install
subparsers:
    cloud-config:
        description: Collection of overcloud configuration tasks
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Tasks Control
              options:
                  tasks:
                      type: ListOfFileNames
                      help: |
                          Provide a option to run one or more tasks to the cloud. Use --help option to print available
                          task. If you run two or more tasks at once, you need to separate them with commas
                          Example: infrared cloud-config --task task1,task3,task2
                          None: Tasks represent playbooks, which are stored in the 'lookup_dir' folder in plugin
                          directory. Task run in the same order as they are provided.
                      lookup_dir: 'post_tasks'