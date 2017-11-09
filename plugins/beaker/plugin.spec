---
config:
    plugin_type: provision
    dependencies:
        - source: ./.library/common
subparsers:
    beaker:
        description: Provision systems using Beaker
        include_groups: ['Ansible options', 'Inventory', 'Common options', 'Answers file']
        groups:
            - title: Beaker instance access details
              options:
                  url:
                      type: Value
                      help: 'URL of Beaker instance'
                      required: True
                  beaker-user:
                      type: Value
                      help: 'Valid username in Beaker instance'
                      default: admin
                      required: True
                  beaker-password:
                      type: Value
                      help: "User's password"
                      required: True
                  web-service:
                      type: Value
                      help: 'For cases where the beaker user is not part of the kerberos system, we require to set the Web service to RPC for authentication rather than rest'
                      default: rpc
                      choices: ['rest', 'rpc']
                      required: True
                  ca-cert:
                      type: Value
                      help: 'For cases where the beaker user is not part of the kerberos system, a CA Certificate is required for authentication with the Beaker server'
                      required: False
                  dry:
                      type: Bool
                      help: 'Skip provisioning/releasing but run rest of playbooks - useful for debugging'
                      default: False
                      required: False

            - title: Details of provisioned host
              options:
                  host-address:
                      type: Value
                      help: 'Address/FQDN of the machine registered in Beaker instance'
                      required: True
                  host-user:
                      type: Value
                      help: 'User to SSH to the host with'
                      default: root
                      required: False
                  host-password:
                      type: Value
                      help: "User's/group's 'Default root password' which is host initially accessible by (can be found in User preferences in web GUI)"
                      required: False

            - title: Base Beaker image to be used for provisioning
              options:
                  image:
                      type: VarFile
                      help: |
                          The image to use for nodes provisioning. Check the "sample.yml.example" for example.
                          Should default to latest RHEL released.
                          __LISTYAMLS__
                      default: 'rhel-7.3'
                      required: False

            - title: Post-deploy options
              options:
                  host-privkey:
                      type: FileValue
                      help: "Specify path to private SSH key to be added to 'hosts' file used later to connect to host where 'host-pubkey' will be inserted"
                      required: True

                  host-pubkey:
                      type: FileValue
                      help: "Specify file with user's public SSH key which will be inserted to authorized_keys of host-user as post-deployment step"
                      required: True

            - title: Host groups
              options:
                  groups:
                      type: ListValue
                      help: |
                          Comma separated list of groups to which your host should be added.
                          For example - baremetal,undercloud,tester.
                          Possible values: baremetal, undercloud, tester, hypervisor.
                      default: baremetal,undercloud,tester

            - title: Release host and return it to Beaker's pool
              options:
                  release:
                      type: Bool
                      help: 'Release system which was previously reserved by beaker-user'
                      default: False
