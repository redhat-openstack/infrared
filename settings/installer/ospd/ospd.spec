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

            - name: Product
              options:
                  - name: product-version
                    help: The product version
                    required: yes
                    choices: ["7", "8", "9", "10"]
                  - name: product-build
                    help: The product build
                    default: latest
                  - name: product-core-version
                    help: The product core version
                    required: yes
                    choices: ["7", "8", "9", "10"]
                  - name: product-core-build
                    help: The product core build
                    default: latest

            - name: Undercloud
              options:
                  - name: undercloud-config
                    complex_type: YamlFile
                    help: The undercloud config details
                    default: default.yml

            - name: Overcloud
              options:
                  - name: overcloud-ssl
                    help: Specifies whether ths SSL should be used for overcloud
                    default: 'no'
                  - name: overcloud-hostname
                    help: Specifies whether we should use custom hostnames for controllers
                    default: 'no'

            - name: Overcloud storage
              options:
                  - name: storage
                    complex_type: YamlFile
                    help: The overcloud storage type
                    default: no-storage.yml

            - name: Product images
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

            - name: Overcloud Network
              options:
                  - name: network-backend
                    help: The overcloud network backend.
                    default: vxlan
                  - name: network-protocol
                    help: The network protocol for overcloud
                    default: ipv4
                  - name: network-isolation
                    complex_type: YamlFile
                    help: The overcloud network isolation type
                    required: yes
                  - name: network-isolation-template
                    complex_type: YamlFile
                    help: The overcloud network isolation template

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
                        - "network-isolation"
                        - "product-core-version"
                        - "product-version"
                        - "images-url"
