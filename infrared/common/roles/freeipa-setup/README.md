FreeIPA Setup
=============

An Ansible role to setup a FreeIPA server

Requirements
------------

This role requires a running host to deploy FreeIPA

Role Variables
--------------

- `freeipa_hostname`: <'ipa.tripleodomain'> -- Hostname for the FreeIPA server
- `freeipa_ip`: <'192.168.24.250'> -- IP for the FreeIPA server
- `directory_manager_password`: <string> -- Password for the directory manager
- `freeipa_admin_password`: <string> -- FreeIPA server admin password
- `undercloud_fqdn`: <'undercloud.tripleodomain'> -- FQDN for the undercloud
- `provisioning_cidr`: <'{{ freeipa_ip }}/24'> -- If set, it adds the given CIDR to the
provisioning interface (which is hardcoded to eth1)
- `supplemental_user`: <stack> The user which is used to deploy FreeIpa on the supplemental node
- `ipa_server_install_params`: <''> -- Additional parameters to pass to the ipa-server-install command
- `prepare_ipa`: If set to true, it will install novajoin or tripleo-ipa in the
  undercloud, and run a script that will create the required privileges/permissions
  in FreeIPA, as well as the undercloud host entry. This requires
  'enable_tls_everywhere' to be set to true, and the following variables to be
  properly defined: 'freeipa_admin_password', 'freeipa_server_hostname',
  'overcloud_cloud_domain', 'undercloud_undercloud_hostname'. If you plan to do
  this yourself, you can set this variable to false. Defaults to true.
- `undercloud_enable_novajoin`: <'true'> -- uses old novajoin service to register
  overcloud nodes into IPA when 'enable_tls_everywhere' is enabled.

Example Playbook
----------------

Sample playbook to call the role

```yaml
# Deploy the FreeIPA Server
- name:  Deploy FreeIPA
  hosts: freeipa_host
  gather_facts: false
  roles:
    - freeipa-setup
```
