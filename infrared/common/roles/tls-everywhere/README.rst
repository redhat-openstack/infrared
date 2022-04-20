===================
TLS Everywhere Role
===================

This role include several stages for setup TLS Everywhere with FreeIPA

General requirements:
``rhos-release`` - repos need to be installed on FreeIpa node, this can be done with rhos-release role.

Roles stages:

``prepare_freeipa`` - Configure and install FreeIPA on the freeipa_node

``set_undercloud_dns`` - Set FreeIPA as the DNS server for the undercloud.

``prepare_undercloud`` - Install novajoin on undercloud node and configure undercloud.

``set_overcloud_dns`` - Set FreeIPA as the DNS server for the overcloud.

``prepare_overcloud`` - Configure overcloud

Example for FreeIPA node setup and Undercloud configuration::

    ---
    - name: Prepare freeipa and undercloud for tls everywhere
      hosts: undercloud
      gather_facts: yes
      any_errors_fatal: true
      tags: tls-everywhere
      roles:
          - role: tls-everywhere
            stages:
                - prepare_freeipa
                - set_undercloud_dns
                - prepare_undercloud


Example for Overcloud configuration::

    ---
    - name: Prepare TLS Everywhere
      hosts: undercloud
      gather_facts: yes
      any_errors_fatal: true
      tasks:
          - include_role:
                name: tls-everywhere
            vars:
                stages:
                    - set_overcloud_dns
                    - prepare_overcloud

Role variables:

``freeipa_node`` - Which node to be used for FreeIPA setup, default is the first node from freeipa group

``freeipa_network_protocol`` - Network protocol, default: ipv4

``freeipa_node_ipaddress`` - Node ip address. It depends of the network protocol

``freeipa_node_ipv4_address`` - Node ipv4 address

``freeipa_setup_script`` - Script for setup FreeIPA, default : https://raw.githubusercontent.com/openstack/tripleo-heat-templates/stable/train/ci/scripts/freeipa_setup.sh

``freeipa_admin_password`` - Admin password, default: 12345678

``freeipa_hosts_secret`` - Host secret, default: redhat

``freeipa_directory_manager_password`` - Directory manager password, default: redhat_01

``freeipa_cloud_domain`` - Cloud domain, default: redhat.local

``freeipa_epel_repo_url`` - EPEL repo url, default: http://ae.mirror.rasanegar.com/fedoraproject/pub/epel/7Server/x86_64/Packages/e/epel-release-7-11.noarch.rpm

``freeipa_undercloud_rc`` - stackrc location, default: '~/stackrc'

``freeipa_undercloud_interface`` - Undercloud external network interface

``freeipa_undercloud_ipaddress`` - Undercloud ip address. It depends of the network protocol

``freeipa_overcloud_deploy_script`` - Overcloud deploy script location, default: ~/overcloud_deploy.sh

``freeipa_templates_basedir`` - Overcloud templates location, default: ~/virt

``freeipa_heat_templates_basedir`` - Overcloud heat templates location, default: /usr/share/openstack-tripleo-heat-templates

``freeipa_use_ceph`` - If setup use ceph storage backend, default: False

``freeipa_network_environment_file``: location of ipv4 network environment file on Undercloud.

``freeipa_network_environment_v6_file``: location of ipv6 network environment file on Undercloud.

``freeipa_forwarder``: The DNS forwarder for BIND, the default is hypervisor. The default will read a nameserver from the hypervisors /etc/resolv.conf
