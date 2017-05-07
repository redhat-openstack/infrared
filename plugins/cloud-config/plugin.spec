---
plugin_type: install
subparsers:
    cloud-config:
        description: Collection of overcloud configuration tasks
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
