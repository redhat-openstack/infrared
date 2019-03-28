=====================
Inventory Update Role
=====================

This role saves Ansible inventory information to the hosts/inventory file. Example for usage:

Using the role in playbook's "roles"::

    ---
    - name: generate inventory file
      hosts: localhost
      gather_facts: no
      tags: always
      roles:
          - role: inventory-update
            inventory_file_name: 'hosts-prov'


Using the role with "include_role"::

    ---
    - include_role:
          name: inventory-update
          apply:
              delegate_to: localhost
      vars:
          inventory_file_name: 'hosts-prov'

Role variables:

``omit_groups`` - List of groups that will be excluded during the inventory file creation.
                  Note: Hosts from the groups will be removed also from the inventory.

``omit_hosts`` - List of hosts that will be excluded during the inventory file creation.

``inventory_file_name`` - Name of the inventory file that will be created. "hosts" file is created from this file.
                          File provide historical overview of the inventory.
