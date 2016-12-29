plugin_type: install
description: Install Tripleo on a designated UnderCloud node
subparsers:
    tripleo:
        # FIXME(yfried): duplicates "description"
        help: Install Tripleo on a designated UnderCloud node
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Undercloud Configuration
              options:
                  config-file:
                      type: Value
                      help: |
                          Path to a custom undercloud.conf file to use for deployment.
                          If not set, it will look under `templates` path for a file named `undercloud.conf`.
                          If no `undercloud.conf` file found, it will use default `/usr/share/instack-undercloud/undercloud.conf.sample`
                          that is provided by the installation.

                  config-options:
                      type: KeyValueList
                      help: |
                          Forces additional Undercloud configuration (undercloud.conf) options.
                          Format: --config-options="section.option=value1;section.option=value".

                  ssl:
                      type: Bool
                      help: |
                          Specifies whether ths SSL should be used for undercloud
                          A self-signed SSL cert will be generated.
                      default: no

            - title: Product
              options:
                  mirror:
                      type: Value
                      help: |
                          Enable usage of specified mirror (for rpm, pip etc) [brq,qeos,tlv - or hostname].
                          (Specified mirror needs to proxy multiple rpm source hosts and pypi packages.)
                      default: ''

                  product-version:
                      type: Value
                      help: |
                          The product version (product == director)
                          Numbers are for OSP releases
                          Names are for RDO releases
                      choices:
                        - "7"
                        - "8"
                        - "9"
                        - "10"
                        - "11"
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                      required: true

                  product-build:
                      help: |
                          "String represents a timestamp of the OSP puddle
                          (for the given product core version).
                          Examples: 'latest', '2016-08-11.1'"
                      type: Value
                      default: latest

                  product-director-build:
                      help: |
                          String represents a timestamp of the OSP-Director puddle (for the given product version)
                          Only applies for OSP releases 7,8,9
                          Examples: 'latest', '2016-08-11.1'"
                      type: Value
                      default: latest

# TODO(yfried): Enable when mixed versions are required
#                  product-director-version:
#                      type: Value
#                      help: |
#                          The director version.
#                          Only applies for OSP releases 7,8,9
#                          If not supplied, same version as 'product-version' will be used when applicable.
#                      choices:
#                        - "7"
#                        - "8"
#                        - "9"

            - title: User
              options:
                  user-name:
                      type: Value
                      help: The installation user name. Will be generated if missing
                      default: stack

                  user-password:
                      type: Value
                      help: The installation user password
                      default: stack

            - title: Custom Repositories
              options:
                  repos-config:
                      type: Value
                      help: |
                          YAML file
                          define new repositories or update exsiting according to file.
                          see documentaion for more details
                  repos-urls:
                      type: Value
                      help: |
                          comma separated list of URLs to download repo files to ``/etc/yum.repos.d``
