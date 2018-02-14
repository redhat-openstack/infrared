RHOS/RDO Version Discovery
--------------------------

This roles discover RHOS/RDO Version and save it in facts as:
    - undercloud_version
    - overcloud_version

Role try to discover the version based on repos names, /etc/rhosp-release and nova version.
The default flow is:
    1. Check yum repos names with regexes:
        - rhel-7-server-openstack-*
        - rhelosp-*
        - rhosp-*
        - rhos-release-rdotrunk*
        - delorean*
        - CentOS-OpenStack*
        - rdo-release*
    2. Check for /etc/rhosp-release and its content
    3. Check nova version and match the RHOS/Version

.. warning:: RDO version discovery works only with repos names.

Default flow can be overwritten with 'discovery_types' variable. Example::

    discovery_types:
        - nova
        - rhos_release_file

Usage examples
==============

1. Run version-discovery with default flow::

    - name: Get the undercloud version
      hosts: undercloud
      gather_facts: yes
      any_errors_fatal: true
      tags: version_discovery
      roles:
          - version-discovery

2. Run version-discovery with 'include_role'::

    - name: Get the undercloud version
      hosts: undercloud
      any_errors_fatal: true
      tasks:
          - include_role:
                name: version-discovery

3. Run version-discovery only to use nova version::

    - name: Get the undercloud version
      hosts: undercloud
      gather_facts: yes
      any_errors_fatal: true
      tags: version_discovery
      vars:
          discovery_types:
              - nova
      roles:
          - version-discovery

Role variables:
===============

``discovery_types`` - List of discovery ways/types to be used. Possible values:
    - repos
    - nova
    - rhos_release_file
