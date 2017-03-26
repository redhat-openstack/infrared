Gabbi Tester
============

Runs telemetry tests against the OpenStack cloud.

Required arguments
------------------

* ``--openstack-version``: The version of the openstack installed.
    That option also defines the list of tests to run against the OpenStack.
* ``--openstackrc``: The `OpenStack RC <http://docs.openstack.org/user-guide/common/cli-set-environment-variables-using-openstack-rc.html>`_ file.
    The absolute and relative paths to the file are supported.  When this option is not provided, `infrared` will try to use the `keystonerc` file from the active workspace.
    The openstackrc file is copied to the tester station and used to run tests
* ``--undercloudrc``: The undercloud RC file.
    The absolute and relative paths to the file are supported.  When this option is not provided, `infrared` will try to use the `stackrc` file from the active workspace.


Optional arguments
------------------
* ``--network``: Network settings to use.
  Default network configuration includes the ``protocol`` (ipv4 or ipv6) and ``interfaces`` sections::

    network:
        protocol: ipv4
        interfaces:
            - net: management
              name: eth1
            - net: external
              name: eth2

* ``--setup``: The setup variables, such as git repo name, folders to use on tester and others::

    setup:
        repo_dest: ~/TelemetryGabbits
        gabbi_venv: ~/gbr
        gabbits_repo: <private-repo-url>


Gabbi results
-------------

`infrared` fetches all the  output files, like results to the ``gabbi_results`` folder under the active `workspace <workspace.html>`_ folder.
