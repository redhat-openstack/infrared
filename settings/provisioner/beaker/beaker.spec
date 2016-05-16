---
command:
    subcommands:
        - name: beaker
          help: Provision systems using Beaker
          include_groups: ['Ansible options', 'Inventory options', 'Common options', 'Configuration file options']
          groups:
              - name: Beaker server
                options:
                    - name: url
                      help: 'The Beaker url'
                      required: True
                    - name: user
                      help: 'Login username to authenticate to Beaker (default: __DEFAULT__)'
                      default: admin
                    - name: password
                      help: 'Password of login user'
                      required: True
                    - name: web-service
                      help: 'For cases where the beaker user is not part of the kerberos system, we require to set the Web service to RPC for authentication rather than rest.'
                      default: 'rest'
                      choices: ['rest', 'rpc']
                    - name: ca-cert
                      help: 'For cases where the beaker user is not part of the kerberos system, a CA Certificate is required for authentication with the Beaker server.'
                      required: False

              - name: Host details
                options:
                    - name: host-address
                      help: 'Address/FQDN of the BM'
                      required: yes
                    - name: host-user
                      help: 'User to SSH to the host with'
                      default: root
                    - name: host-password
                      help: "User's SSH password"
                    - name: host-key
                      help: "User's SSH key"

              - name: Image
                options:
                    - name: image
                      complex_type: YamlFile
                      help: 'The image to use for nodes provisioning. Check the "sample.yml.example" for example.'
                      default: "rhel-7.2.yml"

              - name: Common
                options:
                    - name: cleanup
                      action: store_true
                      help: 'Release the system'
                      nested: no
