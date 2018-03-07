Tempest
=======

Runs Tempest tests against an OpenStack cloud.

Required arguments
------------------

* ``--openstack-installer``: The installer used to deploy OpenStack.
    Enables extra configuration steps for certain installers. Supported installers are: ``tripleo`` and ``packstack``.

* ``--openstack-version``: The version of the OpenStack installed.
    Enables additional configuration steps when version <= 7.

* ``--tests``: The list of test suites to execute. For example: ``network,compute``.
    The complete list of the available suites can be found by running ``ir tempest --help``

* ``--openstackrc``: The `OpenStack RC <http://docs.openstack.org/user-guide/common/cli-set-environment-variables-using-openstack-rc.html>`_ file.
    The absolute and relative paths to the file are supported.  When this option is not provided, `infrared` will try to use the `keystonerc` file from the active workspace.
    The openstackrc file is copied to the tester station and used to configure and run Tempest.


Optional arguments
------------------

The following useful arguments can be provided to tune tempest tester. Complete list of arguments can be found by running ``ir tempest --help``.

* ``--setup``: The setup type for the tempest.
   Can be ``git`` (default), ``rpm`` or pip. Default tempest git repository is `<https://git.openstack.org/openstack/tempest.git>`_. This value can be overridden with the ``--extra-vars`` cli option::

     ir tempest -e setup.repo=my.custom.repo [...]

* ``--revision``: Specifies the revision for the case when tempest is installing from the git repository.
    Default value is ``HEAD``.

* ``--deployer-input-file``: The deployer input file to use for Tempest configuration.
     The absolute and relative paths to the file are supported. When this option is not provided `infrared` will try to use the `deployer-input-file.conf` file from active workspace folder.

     For some OpenStack versions(kilo, juno, liberty) Tempest provides predefined deployer files. Those files can be downloaded from the git repo and passed to the Tempest tester::

        BRANCH=liberty
        wget https://raw.githubusercontent.com/redhat-openstack/tempest/$BRANCH/etc/deployer-input-$BRANCH.conf
        ir tempest --tests=sanity \
                   --openstack-version=8 \
                   --openstack-installer=tripleo \
                   --deployer-input-file=deployer-input-$BRANCH.conf

* ``--image``: Image to be uploaded to glance and used for testing. Path have to be a url.
    If image is not provided, tempest config will use the default.

.. note:: You can specify image ssh user with ``--config-options compute.image_ssh_user=``

Tempest results
---------------

`infrared` fetches all the tempest output files, like results to the ``tempest_results`` folder under the active `workspace <workspace.html>`_ folder::

    ll .workspace/my_workspace/tempest_results/tempest-*

    -rw-rw-r--. tempest-results-minimal.xml
    -rw-rw-r--. tempest-results-neutron.xml

Downstream tests
----------------

The tempest plugin provides the ``--plugin`` cli option which can be used to
specify the plugin url to install. This option can be used, for example, to specify
a downstream repo with tempest tests and run them::

        ir tempest --tests=neutron_downstream \
                   --openstack-version=12 \
                   --openstack-installer=tripleo \
                   --plugin=https://downstrem.repo/tempest_neutron_plugin \
                   --setup rpm

The plugin flag can also specify version of plugin to clone by separating
the url and version with a comma::

        ir tempest --tests=neutron_downstream \
                   --openstack-version=12 \
                   --openstack-installer=tripleo \
                   --plugin=https://downstrem.repo/tempest_neutron_plugin,osp10 \
                   --setup rpm

The neutron_downstream.yml file can reference the upstream project in case the
downstream repo is dependant or imports any upstream modules::

    ---
    test_dict:
        test_regex: ''
        whitelist:
            - "^neutron_plugin.tests.scenario.*"
        blacklist:
            - "^tempest.api.network.*"
            - "^tempest.scenario.test_network_basic_ops.test_hotplug_nic"
            - "^tempest.scenario.test_network_basic_ops.test_update_instance_port_admin_state"
            - "^tempest.scenario.test_network_basic_ops.test_port_security_macspoofing_port"
        plugins:
            upstream_neutron:
                repo: "https://github.com/openstack/neutron.git"

