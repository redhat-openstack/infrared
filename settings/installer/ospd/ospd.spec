---
subparsers:
    ospd:
        help: Installs openstack using OSP Director
        include_groups: ['Ansible options', 'Inventory hosts options', 'Common options', 'Configuration file options']
        groups:
            - title: Introspection
              options:
                  instackenv-file:
                      type: Value
                      help: The path to the instackenv.json configuration file used for introspection.

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
                      help: The product version (product == director)
                      choices: ["7", "8", "9", "10"]
                      default: 9

                  product-build:
                      type: Value
                      help: "String represents a timestamp of the OSP-Director puddle (for the given product version). Relevant only for OSP 9 and below. Examples: 'latest', '2016-08-11.1'"
                      default: latest

                  product-core-version:
                      type: Value
                      help: The product core version (product-core == overcloud)
                      choices: ["7", "8", "9", "10"]
                      default: 9

                  product-core-build:
                      type: Value
                      help: "String represents a timestamp of the OSP puddle (for the given product core version). Examples: 'latest', '2016-08-11.1'"
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

                  network-lbaas:
                      type: Value
                      help: Activate Neutron LBaaS(v2) extension on the OverCloud.
                      choices: ['yes', 'no']
                      default: 'no'

                  public-network:
                      type: Value
                      help: Deploy "public" external network on the OverCloud as post-install.
                      choices: ['yes', 'no']
                      default: 'yes'

                  public-subnet:
                      type: YamlFile
                      help: |
                          Subnet detail for "public" external network on the OverCloud as post-install.
                          CIDR
                          Allocation Pool
                          Gateway
                      default: default.yml

            - title: Overcloud storage
              options:
                  storage-backend:
                      type: Value
                      choices: ['ceph', 'ceph2', 'swift', 'netapp-iscsi', 'netapp-nfs', 'lvm']
                      default: 'lvm'
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

                images-update:
                    type: Value
                    help: |
                        Update OverCloud image before deploying, to match core build.
                        Note: This can take a while and is not 100%% stable due to old libguestfs on RHEL-7.2
                    choices: ['no', 'yes', 'verbose']
                    default: 'no'

                images-cleanup:
                    type: Value
                    help: |
                        Removes all the downloaded images when images-task is in 'rpm' or 'import'
                    choices: ['no', 'yes']
                    default: 'yes'

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
