---
subparsers:
    ospd:
        help: Installs openstack using OSP Director
        include_groups: ['Ansible options', 'Inventory hosts options', 'Common options', 'Configuration file options']
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

                  overcloud-fencing:
                      type: Value
                      help: Specifies whether fencing should be configured for overcloud nodes
                      default: 'no'

                  overcloud-hostname:
                      type: YamlFile
                      help: |
                            Provide a template for customized hostnames.
                            See documentation for further details.
                            NOTE: requires product-version > 7

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
                      choices: ['ceph', 'swift', 'netapp-iscsi', 'netapp-nfs']
                      help: |
                        The storage that we would like to use.
                        If not supplied, OSPD will default to local LVM on the controllers.
                        NOTE: when not using external storage, this will set the default for "--storage-nodes" to 1.

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
                    required_when: "images-task == import"

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

            - title: Cleanup
              options:
                  cleanup:
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      silent:
                          - "deployment-files"
                          - "images-url"
