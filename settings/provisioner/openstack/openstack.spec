---
subparsers:
    openstack:
        help: Provision systems using Ansible OpenStack modules
        groups:
            - title: cloud
              options:
                  cloud:
                      type: Value
                      help: "The cloud which the OpenStack modules will operate against. Cloud setup instructions: http://docs.openstack.org/developer/os-client-config/#config-files"
                      required: yes
            - title: prefix
              options:
                  prefix:
                      type: Value
                      help: An prefix which would be contacted to each provisioned resource. An random prefix would be generated in case this value is not specified.
            - title: image
              options:
                  image:
                      type: Value
                      help: An image id or name, on OpenStack cloud to provision the instance with. To see full list of images avaialable on the cloud, use 'glance image-list'.
                      required: yes
            - title: topology
              options:
                  neutron:
                      type: YamlFile
                      help: Network resources
                      default: default.yml
                  nodes:
                      type: Topology
                      help: Provision topology.
                      default: "1_controller"
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
