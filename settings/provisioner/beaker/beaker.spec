---
subparsers:
    beaker:
        help: Provision systems using Beaker
        include_groups: ['Ansible options', 'Inventory options', 'Common options', 'Configuration file options']
        groups:
            - title: Beaker server
              options:
                  url:
                      type: Value
                      help: 'The Beaker url'
                      required: True
                  user:
                      type: Value
                      help: 'Login username to authenticate to Beaker'
                      default: admin
                  password:
                      type: Value
                      help: 'Password of login user'
                      required: True
                  web-service:
                      type: Value
                      help: 'For cases where the beaker user is not part of the kerberos system, we require to set the Web service to RPC for authentication rather than rest.'
                      default: 'rest'
                      choices: ['rest', 'rpc']
                  ca-cert:
                      type: Value
                      help: 'For cases where the beaker user is not part of the kerberos system, a CA Certificate is required for authentication with the Beaker server.'
                      required: False

            - title: Host details
              options:
                  host-address:
                      type: Value
                      help: 'Address/FQDN of the BM'
                      required: yes
                  host-user:
                      type: Value
                      help: 'User to SSH to the host with'
                      default: root
                  host-password:
                      type: Value
                      help: "User's SSH password"
                  host-key:
                      type: Value
                      help: "User's SSH key"

            - title: image
              options:
                  image:
                      type: YamlFile
                      help: 'The image to use for nodes provisioning. Check the "sample.yml.example" for example.'
                      default: "rhel-7.2.yml"

            - title: Cleanup
              options:
                  cleanup:
                      action: store_true
                      help: 'Release the system'
