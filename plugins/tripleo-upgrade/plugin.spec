plugin_type: install
description: Major version upgrade of Tripleo deployment
subparsers:
    tripleo-upgrade:
        help: |
            Major version upgrade of Tripleo deployment.
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Upgrade Options
              options:
                  version:
                      type: Value
                      help: |
                          The product version (product == director)
                          Numbers are for OSP releases
                          Note: Currently, there is upgrade possibility from version 9 to version 10 only.
                      choices:
                        - "10"
                  deployment-script:
                      type: Value
                      help: |
                          Location of the overcloud_deploy.sh script used during Tripleo Deployment
                      default: "~/overcloud_deploy.sh"