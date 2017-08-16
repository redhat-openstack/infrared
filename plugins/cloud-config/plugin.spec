---
plugin_type: install
subparsers:
    cloud-config:
        description: Collection of overcloud configuration tasks
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Stages Control
              options:
                  tasks:
                      type: ListOfFileNames
                      help: Specify a list of task to execute
                      lookup_dir: 'post_tasks'