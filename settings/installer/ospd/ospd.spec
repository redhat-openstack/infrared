---
subparsers:
    ospd:
        formatter_class: RawTextHelpFormatter
        help: Installs openstack using OSP Director
        groups:
            - title: Firewall
              options:
                  firewall:
                      type: YamlFile
                      help: The firewall configuration
                      default: default.yml

            - title: Introspection
              options:
                  instackenv-file:
                      type: Value
                      help: |
                            The path to the instackenv.json configuration file used for introspection.
                            If not set, it will look under the `deployment-files` path for the instackenv.json file.

            - title: Undercloud configuration
              options:
                  undercloud-config:
                      type: Value
                      help: |
                          Path to our custom undercloud.conf file that we wish to use for our deployment.
                          If not set, it will look under the `templates` path for a file named `undercloud.conf`.
                          If no `undercloud.conf` file found, it will use the default `/usr/share/instack-undercloud/undercloud.conf.sample`
                          that is provided by the installation.

            - title: Deployment Files
              options:
                  deployment-files:
                      type: Value
                      help: |
                            The absolute path to the folder containing the templates of the overcloud deployment.
                            Please see `settings/installer/ospd/deployment/example` as reference.
                      required: yes

            - title: Product
              options:
                  product-version:
                      type: Value
                      help: The product version
                      choices: ["7", "8", "9", "10"]
                      default: 8

                  product-build:
                      type: Value
                      help: The product build
                      default: latest

                  product-core-version:
                      type: Value
                      help: The product core version
                      choices: ["7", "8", "9", "10"]
                      default: 8

                  product-core-build:
                      type: Value
                      help: The product core build
                      default: latest

            - title: Amount of nodes to use for deployment
              options:
                  controller-nodes:
                      type: Value
                      help: The amount of controller nodes to deploy

                  compute-nodes:
                      type: Value
                      help: The amount of compute nodes to deploy

                  storage-nodes:
                      type: Value
                      help: |
                            The amount of storage nodes to deploy. If --storage-backend is set, this
                            value will default to '1', otherwise no storage nodes will be used.

            - title: Overcloud
              options:
                  overcloud-ssl:
                      type: Value
                      help: Specifies whether ths SSL should be used for overcloud
                      default: 'no'

                  overcloud-hostname:
                      type: Value
                      help: Specifies whether we should use custom hostnames for controllers
                      default: 'no'

                  overcloud-script:
                      type: Value
                      help: |
                            The absolute path to a custom overcloud deployment script.
                            If not set, it will auto generate a deployment according to the
                            provided templates / options.

            - title: Overcloud Network Isolation
              options:
                  network-backend:
                      type: Value
                      help: The overcloud network backend.
                      choices: ['gre', 'vxlan', 'vlan']
                      default: vxlan

                  network-protocol:
                      type: Value
                      help: The overcloud network backend.
                      choices: ['ipv4', 'ipv6']
                      default: 'ipv4'

            - title: Overcloud storage
              options:
                  storage-backend:
                      type: Value
                      help: The storage that we would like to use. Default to local LVM on the controllers.
                      choices: ['ceph', 'swift', 'netapp-iscsi', 'netapp-nfs']

                  storage-external:
                      type: Value
                      help: Whether to use an external storage rather than setting it up with the director
                      choices: ['no', 'yes']
                      default: 'no'

            - title: Overcloud images
              options:
                images-task:
                    type: Value
                    help: |
                        Specifies the source for the OverCloud images:
                        * RPM - packaged with product (versions 8 and above)
                        * IMPORT - fetch from external source (versions 7 and 8). Requires to specify '--image-url'.
                        * BUILD - build images locally (takes longer)
                    choices: [import, build, rpm]
                    default: rpm

                images-url:
                    type: Value
                    help: Specifies the import image url. Required only when images task is 'import'

            - title: User
              options:
                  user-name:
                      type: Value
                      help: The installation user name
                      default: stack

                  user-password:
                      type: Value
                      help: The installation user password
                      default: stack

            - title: Loadbalancer
              options:
                  loadbalancer:
                      type: YamlFile
                      help: The loadbalancer to use

            - title: Workarounds
              options:
                  workarounds:
                      type: YamlFile
                      help: The list of workarounds to use during install

            - title: common
              options:
                  dry-run:
                      action: store_true
                      help: Only generate settings, skip the playbook execution stage
                  cleanup:
                      action: store_true
                      help: Clean given system instead of provisioning a new one
                  input:
                      action: append
                      type: str
                      short: i
                      help: Input settings file to be loaded before the merging of user args
                  output:
                      type: str
                      short: o
                      help: 'File to dump the generated settings into (default: stdout)'
                  extra-vars:
                      action: append
                      short: e
                      help: Extra variables to be merged last
                      type: str
                  from-file:
                      type: IniFile
                      help: the ini file with the list of arguments
                  generate-conf-file:
                      type: str
                      help: generate configuration file (ini) containing default values and exits. This file is than can be used with the from-file argument
