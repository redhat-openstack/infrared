---
command:
    subcommands:
        - name: ospd
          help: Installs openstack using OSP Director
          include_groups: ['Inventory arguments', 'Common arguments', 'Configuration file arguments']
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
                    choices: ["7", "8", "9"]
                  - name: product-build
                    help: The product build
                    default: latest
                  - name: product-core-version
                    help: The product core version
                    required: yes
                    choices: ["7", "8", "9"]
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

            - name: Overcloud storage
              options:
                  - name: storage
                    complex_type: YamlFile
                    help: The overcloud storage type
                    default: no-storage.yml

            - name: Product images
              options:
                  - name: images-task
                    help: Specifies whether the images should be built or imported
                    required: yes
                    choices: [import, build]
                  - name: images-url
                    help: Specifies the import image url. Required only when images task is 'import'

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
