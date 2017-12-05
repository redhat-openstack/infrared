Virtualbmc role
---------------

This roles installs python-virtualbmc package and configures it for all the
overcloud nodes hosted on the hypervisor. Should be run on the undercloud node.

By default this role install vbmc on the hypervisor. Target host can be changed
by setting the vbmc_host value to 'undercloud'.

Usage examples
==============

1. Run default vbmc configuration::

    - name: Configure vbmc
      hosts: undercloud
      any_errors_fatal: true
      tasks:
          - include_role:
                name: vbmc
            vars:
                vbmc_nodes: "{{ groups.get('overcloud_nodes', []) }}"

2. Setup vbmc on the undercloud::

    - name: Configure vbmc
      hosts: undercloud
      any_errors_fatal: true
      tasks:
          - include_role:
                name: vbmc
            vars:
                vbmc_nodes: "{{ groups.get('overcloud_nodes', []) }}"
                vbmc_host: undercloud
