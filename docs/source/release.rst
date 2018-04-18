.. include:: warning.txt

Release Notes
=============

v1.1.0
------

New Features
^^^^^^^^^^^^

* Added support for OSPD on Bare-Metal machines (documentation pending).
* Move to GerritHub
* Improve Documentaion
* Unit-Testing via tox
* OSPD
    * Internal Swift storage backend
    * Older OverCloud versions with New UnderCloud (OSP-d #8 and above).
      For example: Deploy OverCloud of OSP #7 with OPS-d #8 UnderCloud
* Scale
    * Internal Ceph
    * Internal Swift
    * Compute
* Collect logs - ansible playbook to grab required data and logs from all nodes post run. Allows to debug the setup even after it was destroyed::

    ansible-playbook -i hosts -e @SETTINGS_YAML_FILE playbooks/collect-logs.yml

  Jobs can now ship logs to Logstash cluster
* Help for arguments of type ``YamlFileArgumet`` lists available files from default locations.
* Reprovision via Foreman and IPMI
* Reprovision and reserve via Beaker
* Configure multiple ``settings`` trees. Will look for file arguments in multiple settings directories as listed in ``infrared.cfg``
* Generate better config files:
    * Put all the required arguments to the generated config ini file
    * If default value is not provided - put the placeholder for that parameter in ini file
    * Resolve only current spec arguments.
    * Infrared allows to use ir-* command in two steps::

      ir-* --generate-conf-file=file.ini
      ir-* --from-file=file.ini
* Use existing image snapshots with ``virsh`` provisioner (faster than building the images)
* ``openstack`` provisioner accepts private DNS server address.
* Add Ansible tags to  ``ospd`` workflow so advanced users can ivoke partial ospd tasks (``undercloud``, ``introspection``, ``overcloud``, etc...)
* Add Tempest tester::

  ir-tester tempest --help
* Customized hostnames for controller nodes
* Adds support for OSP #10
* OSPD post-install actions no longer invoked during ``ir-installer ospd`` run. Need to be explictly invoked via advanced Ansible call::

    ansible-playbook -i hosts -e @SETTINGS_YAML_FILE playbooks/installer/ospd/post_install/ACTION.yml
* Configure fencing of overcloud nodes (virsh only) with post-install playbook.
* Invetory files created for each invocation (``hosts-provisioner`` and ``hosts-installer`` are created, instead of overwriting the same ``hosts-$USER`` file.)



Bug Fixes
^^^^^^^^^

* SSH to OverCloud nodes:
  OSPD reprovisions OverCloud machines with new addresses and credentials.
  Final stage of install uses built-in openstack module to get OverCloud info from UnderCloud (``nova list``) and recreate invetory and ssh config files.
* Version conflicts:
    * pin ``Babel``
    * Removed ``configure`` module
    * Blacklist ``Ansible`` 2.1.0
    * pin ``shade``
* Default config file is up to date
* Packstack:
    * Added All-In-One (``aio.yml``) topology support
    * Fixed network tasks on controller (No longer support dedicated network nodes)
* Collect Logs: Avoid archiving virsh machines on ``virthost`` node.
* Improve lookup: No longer fails when there are multiple visits to the same key in the lookup
* Faster lookup with unittest.
* ``virsh`` provisioner no longer fails if ``sshpass`` is not installed
* Remove "sample" files from genertad config files.
* Resolve ``~`` (expanduser) on ``extra-vars`` file input (``--extra-vars @~/my/file``)
* Informative failure message for bad topology syntax
* Single default inventory file for all ``ir-*`` tools
* Beaker - Proper Ansible failure message when ``ca_cert`` file is missing
* Remove empty placeholer file for rhos-8.0 workarounds
* ``openstack`` provisioner no longer registers the same IP address for instances of the same node
* Fix internal ceph backend: ``glance image-create`` no longer fails with ceph backend
* Fix merging lists in inpute files.
* ``rhos-release`` should pin latest version
* Verify that ``overcloudrc`` file is created after overcloud deployment succeeds
* Install python-virtualenv on the undercloud (required for ``shade``)
* Add ipv6 support for virsh external network
* Cast the string value of ``product`` to int
