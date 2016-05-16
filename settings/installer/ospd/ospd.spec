---
command:
    subcommands:
        - name: ospd
          help: Installs openstack using OSP Director
          include_groups: ['Ansible options', 'Inventory options', 'Common options', 'Configuration file options']
          groups:
              - name: Firewall
                options:
                    - name: firewall
                      complex_type: YamlFile
                      help: The firewall configuration
                      default: default.yml

              - name: Introspection
                options:
                    - name: instackenv-file
                      help: |
                            The path to the instackenv.json configuration file used for introspection.
                            If not set, it will look under the `deployment-files` path for the instackenv.json file.

              - name: Undercloud configuration
                options:
                    - name: undercloud-config
                      help: |
                            Path to our custom undercloud.conf file that we wish to use for our deployment.
                            If not set, it will look under the `templates` path for a file named `undercloud.conf`.
                            If no `undercloud.conf` file found, it will use the default `/usr/share/instack-undercloud/undercloud.conf.sample`
                            that is provided by the installation.

              - name: Deployment Files
                options:
                    - name: deployment-files
                      help: |
                            The absolute path to the folder containing the templates of the overcloud deployment.
                            Please see `settings/installer/ospd/deployment/example` as reference.
                      required: yes

              - name: Product
                options:
                    - name: product-version
                      help: The product version
                      choices: ["7", "8", "9", "10"]
                      default: 8

                    - name: product-build
                      help: The product build
                      default: latest

                    - name: product-core-version
                      help: The product core version
                      choices: ["7", "8", "9", "10"]
                      default: 8

                    - name: product-core-build
                      help: The product core build
                      default: latest

              - name: Amount of nodes to use for deployment
                options:
                    - name: controller-nodes
                      help: The amount of controller nodes to deploy
                    - name: compute-nodes
                      help: The amount of compute nodes to deploy
                    - name: storage-nodes
                      help: |
                            The amount of storage nodes to deploy. If --storage-backend is set, this
                            value will default to '1', otherwise no storage nodes will be used.

              - name: Overcloud
                options:
                    - name: overcloud-ssl
                      help: Specifies whether ths SSL should be used for overcloud
                      default: 'no'

                    - name: overcloud-fencing
                      help: Specifies whether fencing should be configured for overcloud nodes
                      default: 'no'

                    - name: overcloud-hostname
                      help: Specifies whether we should use custom hostnames for controllers
                      default: 'no'

                    - name: overcloud-script
                      help: |
                            The absolute path to a custom overcloud deployment script.
                            If not set, it will auto generate a deployment according to the
                            provided templates / options.

              - name: Overcloud Network Isolation
                options:
                    - name: network-backend
                      help: The overcloud network backend.
                      choices: ['gre', 'vxlan', 'vlan']
                      default: vxlan

                    - name: network-protocol
                      help: The overcloud network backend.
                      choices: ['ipv4', 'ipv6']
                      default: 'ipv4'

              - name: Overcloud storage
                options:
                    - name: storage-backend
                      choices: ['ceph', 'swift', 'netapp-iscsi', 'netapp-nfs']
                      help: |
                        The storage that we would like to use.
                        If not supplied, OSPD will default to local LVM on the controllers.
                        NOTE: when not using external storage, this will set the default for "--storage-nodes" to 1.

                    - name: storage-external
                      help: Whether to use an external storage rather than setting it up with the director
                      choices: ['no', 'yes']
                      default: 'no'

              - name: Overcloud images
                options:
                    - name: images-task
                      help: |
                          Specifies the source for the OverCloud images:
                          * RPM - packaged with product (versions 8 and above)
                          * IMPORT - fetch from external source (versions 7 and 8). Requires to specify '--image-url'.
                          * BUILD - build images locally (takes longer)
                      choices: [import, build, rpm]
                      default: rpm

                    - name: images-url
                      help: Specifies the import image url. Required only when images task is 'import'
                      required_when: "images-task == import"

              - name: User
                options:
                    - name: user-name
                      help: The installation user name
                      default: stack

                    - name: user-password
                      help: The installation user password
                      default: stack

              - name: Loadbalancer
                options:
                    - name: loadbalancer
                      complex_type: YamlFile
                      help: The loadbalancer to use

              - name: Workarounds
                options:
                    - name: workarounds
                      complex_type: YamlFile
                      help: The list of workarounds to use during install

              - name: Cleanup
                options:
                    - name: cleanup
                      action: store_true
                      help: Clean given system instead of running playbooks on a new one.
                      nested: no
                      silent:
                          - "deployment-files"
                          - "images-url"
