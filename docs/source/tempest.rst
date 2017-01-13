Tempest
=======

Runs tempest tests against the OpenStack.

Required arguments
------------------

* ``--openstack-installer``: The installer used to deploy OpenStack.
    This options enables extra configuration steps for certain installers. Supported installers are: ``tripleo`` and ``packstack``.

* ``--openstack-version``: The version of the openstack installed.
    Enables additional configuration steps when version <= 7.

* ``--tests``: The list of test suites to execute. For example: ``network,compute``.
    The complete list of the available suites can be found by running ``ir tempest --help``


Optional arguments
------------------

The following useful arguments can be provided to tune tempest tester. Complete list of arguments can be found by running ``ir tempest --help``.

* ``--setup``: The setup type for the tempest.
   Can be ``git`` (default) or ``rpm``. Default tempest git repository is `<https://github.com/redhat-openstack/tempest.git>`_. This value can be overridden with the ``--extra-vars`` cli option::

     ir tempest -e setup.repo=my.custom.repo [...]

* ``--revision``: Specifies the revision for the case when tempest is installing from the git repository.
    Default value is ``HEAD``.


Tempest results
---------------

Infrared fetches all the tempest output files, like results to the ``tempest_results`` folder under the active `profile <profile.html>`_ folder::

    ll .profile/my_profile/tempest_results/tempest-*

    -rw-rw-r--. tempest-results-minimal.xml
    -rw-rw-r--. tempest-results-neutron.xml

