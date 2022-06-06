TripleO Undercloud
==================

Deploys a TripleO undercloud

Setup an Undercloud
-------------------

* ``--version``: TripleO release to install.
    Accepts either an integer for RHEL-OSP release, or a community release
    name (``Liberty``, ``Mitaka``, ``Newton``, etc...) for RDO release

* ``--build``: Specify a build date or a label for the repositories.
    Supports any rhos-release labels.
    Examples: ``passed_phase1``, ``2016-08-11.1``, ``Y1``, ``Z3``, ``GA``
    Not used in case of RDO.

* ``--buildmods``: Let you the option to add flags to rhos-release:

    | ``pin`` - Pin puddle (dereference 'latest' links to prevent content from changing). This is the default flag.
    | ``flea`` - Enable flea repos.
    | ``unstable`` - This will enable brew repos or poodles (in old releases).
    | ``none`` - Use none of those flags.

 .. note:: ``--buildmods`` and ``--build`` flags are for internal Red Hat users only.

* ``--enable-testing-repos``: Let you the option to enable testing/pending repos with rhos-release. Multiple values
    have to be coma separated.
    Examples: ``--enable-testing-repos rhel,extras,ceph`` or ``--enable-testing-repos all``

* ``--cdn`` Register the undercloud with a Red Hat Subscription Management platform.
    Accepts a file with subscription details.

      .. code-block:: yaml
         :caption: cdn_creds.yml

          server_hostname: example.redhat.com
          username: user
          password: HIDDEN_PASS
          autosubscribe: yes
          server_insecure: yes

    For the full list of supported input, see the `module documentation`_.

    .. note:: Pre-registered undercloud are also supported if ``--cdn`` flag is missing.
    .. warning:: The contents of the file are hidden from the logged output, to protect private account credentials.

* ``--from-source`` Build tripleo components from the upstream git repository.
    Accepts list of tripleo components. The delorean project is used to build rpm packages. For more information about
    delorean, visit `Delorean documentation <http://dlrn.readthedocs.io/en/latest>`_.

    To deploy specific tripleo components from git repository::

      infrared tripleo-undercloud --version 13 \
        --from-source name=openstack/python-tripleoclient \
        --from-source name=openstack/neutron,refs=refs/changes/REF_ID \
        --from-source name=openstack/puppet-neutron

    .. note::
         - This feature is supported by OSP 13 or RDO queens versions.
         - This feature is experimental and should be used only for development.

* ``--custom-sources-script-url`` setup custom repos (package sources) by a custom user provided script.
    This way allows to not have any internal infrastructure related logic included,
    and at the same able provides the flexibility to mix released and not released content as you wish. ::

        infrared tripleo-undercloud --version 17 \
        --custom-sources-script-url http://mysuperscriptstope.example.org/script_generator?foobar=32 \
        --custom-sources-script-args '--delorian_id 42' \

    Infrared  also provides environment variables to the custom script about the execution context,
    for example 'REPO_OS_VERSION' holds the version which was passed to the install script.

    .. note::
         - This feature is expiremental therefore the behavior may change

.. _module documentation: http://docs.ansible.com/ansible/redhat_subscription_module.html

.. note:: | In case of **virsh** deployment **ipxe-roms-qemu** will be installed on hypervisor node.
          | This package can be found in a **rhel-server** repo in case of RedHat and in **Base** repo in case of CentOS

To deploy a working undercloud::

  infrared tripleo-undercloud --version 10

For better fine-tuning of packages, see `custom repositories`_.

Overcloud Images
----------------
The final part of the undercloud installation calls for creating the images from which the OverCloud
will be later created.

* Depending on ``--images-task`` these the undercloud can be either:

    * ``build`` images:
        Build the overcloud images from a fresh guest image.
        To use a different image than the default CentOS cloud
        guest image, use ``--images-url`` to define base image than CentOS.
        For OSP installation, you must provide a url of a valid RHEL image.
    * ``import`` images from url:
        Download pre-built images from a given ``--images-url``.
    * Download images via ``rpm``:
        Starting from OSP 8, TripleO is packages with pre-built images available via RPM.

        To use different RPM, use ``--images-url`` to define the location of the RPM. You need
        to provide all dependencies of the remote RPM. Locations have to be separated with comma

        .. note:: This option is invalid for `RDO` installation.

* Use ``--images-packages`` to define a list of additional packages to install on the OverCloud image.
  Packages can be specified by name or by providing direct url to the rpm file.
* Use ``--images-remove-packages`` to define a list of packages to uninstall from the OverCloud image.
  Packages must be specified by name.
* Use ``--images-remove-no-deps-packages`` to define a list of packages to force uninstall from the overcloud image.
  Packages must be specified by name and seperated by a comma.
  This is useful in a scenario where there is a requirment to uninstall a certain RPM package without removing its dependencies.

  .. note:: This task executes `rpm -e --nodeps` command which will cause RPM DB to be out of sync

* ``--images-cleanup`` tells `infrared` do remove the images files original after they are uploaded
  to the undercloud's Glance service.

To configure overcloud images::

  infrared tripleo-undercloud --images-task rpm

.. note:: This assumes an undercloud was already installed and
    will skip `installation <tripleo-undercloud.html#Setup an Undercloud>`_ stage
    because ``--version`` is missing.

When using RDO (or for OSP 7), ``rpm`` strategy in unavailable. Use ``import`` with ``--images-url`` to download
overcloud images from web::

  infrared tripleo-undercloud --images-task import --images-url http://buildlogs.centos.org/centos/7/cloud/x86_64/tripleo_images/mitaka/delorean

.. note:: The RDO overcloud images can be also found here: https://images.rdoproject.org

If pre-packaged images are unavailable, tripleo can build the images locally on top of a regular cloud guest image::

  infrared tripleo-undercloud --images-task build

CentOS or RHEL guest images will be used for RDO and OSP respectively.
To use a different image specify ``--images-url``::

  infrared tripleo-undercloud --images-task build --images-url http://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2

.. note:: building the images takes a long time and it's usually quicker to download them.

In order to update default overcloud image kernel provided by sources (for example RPM), with the latest kernel present on overcloud image,
specify ``overcloud-update-kernel``.

.. note:: when installing kernel-rt inside overcloud guest image, the latest RealTime kernel will be used instead of default kernel.


See the `RDO deployment <rdo.html>`_ page for more details on how to setup RDO product.

Undercloud Configuration
------------------------

Undercloud is configured according to ``undercloud.conf`` file.
Use ``--config-file`` to provide this file, or let `infrared` generate one automatically, based on
a sample file provided by the project.
Use ``--config-options`` to provide a list of ``section.option=value`` that will override
specific fields in it.

Use the ``--ssl=yes`` option to install enable SSL on the undercloud. If used, a self-signed SSL cert will be generated.

Custom Repositories
-------------------

Add custom repositories to the undercloud, after `installing the TripleO repositories <tripleo-undercloud.html#Setup an Undercloud>`_.

* ``--repos-config`` setup repos using the ansible yum_repository module.
    Using this option enables you to set specific options for each repository:

      .. code-block:: yaml
         :caption: repos_config.yml

          ---
          extra_repos:
              - name: my_repo1
                file: my_repo1.file
                description: my repo1
                baseurl: http://myurl.com/my_repo1
                enabled: 0
                gpgcheck: 0
              - name: my_repo2
                file: my_repo2.file
                description: my repo2
                baseurl: http://myurl.com/my_repo2
                enabled: 0
                gpgcheck: 0
              ...

      .. note:: This explicitly supports some of the options found in
        yum_repository module (name, file, description, baseurl, enabled and gpgcheck).
        For more information about this module, visit `Ansible yum_repository documentation <https://docs.ansible.com/ansible/yum_repository_module.html>`_.

      .. note:: Custom repos generate by ``--repos-config`` can be uploaded to Overcloud guest image by specifying ``--upload-extra-repos true``

* ``repos-urls``: comma separated list of URLs to download repo files to ``/etc/yum.repos.d``

Both options can be used together::

  infrared tripleo-undercloud [...] --repos-config repos_config.yml --repos-urls "http://yoururl.com/repofile1.repo,http://yoururl.com/repofile2.repo"


TripleO Undercloud User
-----------------------
``--user-name`` and ``--user-password`` define a user, with password,
for the undercloud. According to TripleO guidelines, the default username is ``stack``.
User will be created if necessary.
.. note:: Stack user password needs to be changed in case of public deployments

Backup
------
When working on a virtual environment, `infrared` can create a snapshot of the installed undercloud that can be later used
to `restore`_ it on a future run, thus saving installation time.

In order to use this feature, first follow the `Setup an Undercloud`_ section.
Once an undercloud VM is up and ready, run the following::

    ir tripleo-undercloud --snapshot-backup yes

Or optionally, provide the file name of the image to create (defaults to "undercloud-snapshot.qcow2").
.. note:: the filename refers to a path on the hypervisor.

    ir tripleo-undercloud --snapshot-backup yes --snapshot-filename custom-name.qcow2

This will prepare a qcow2 image of your undercloud ready for usage with `Restore`_.

.. note:: this assumes an undercloud is already installed and will skip
    `installation <tripleo-undercloud.html#Setup an Undercloud>`_ and `images <tripleo-undercloud.html#Overcloud Images>`_ stages.

Restore
-------
When working on a virtual environment, `infrared` can use a pre-made undercloud image to quickly set up an environment.
To use this feature, simply run::

    ir tripleo-undercloud --snapshot-restore yes

Or optionally, provide the file name of the image to restore from (defaults to "undercloud-snapshot.qcow2").
.. note:: the filename refers to a path on the hypervisor.

Undercloud Upgrade
---------------------
Upgrade is discovering current Undercloud version and upgrade it to the next major one.
To upgrade Undercloud run the following command::

    infrared tripleo-undercloud -v --upgrade yes

.. note:: The `Overcloud <tripleo-overcloud.html>`_ won't need new images to upgrade to. But you'd need to upgrade
    the images for OC nodes before you attempt to scale out nodes. Example for Undercloud upgrade and images update::

        infrared tripleo-undercloud -v --upgrade yes --images-task rpm

.. warning:: Currently, there is upgrade possibility from version 9 to version 10 only.

.. warning:: Upgrading from version 11 to version 12 isn't supported via the tripleo-undercloud plugin anymore. Please
     check the tripleo-upgrade plugin for 11 to 12 `upgrade instructions <tripleo_upgrade.html>`_.

Undercloud Update
---------------------
Update is discovering current Undercloud version and perform minor version update.
To update Undercloud run the following command::

    infrared tripleo-undercloud -v --update-undercloud yes

Example for update of Undercloud and Images::

        infrared tripleo-undercloud -v --update-undercloud yes --images-task rpm

.. warning:: Infrared support update for RHOSP from version 8.

Undercloud Workarounds
----------------------
Allow injecting workarounds defined in an external file before/after the undercloud installation::

    infrared tripleo-undercloud -v --workarounds 'http://server.localdomain/workarounds.yml'

The workarounds can be either patches posted on review.openstack.org or arbitrary shell commands.
Below is an example of a workarounds file::

        ---
        pre_undercloud_deploy_workarounds:

          - BZ#1623061:
             patch: false
             basedir: ''
             id: ''
             # patchlevel is optional and defaults to 1
             patchlevel: 2
             command: 'touch /home/stack/pre_workaround_applied'

        post_undercloud_deploy_workarounds:

          - BZ#1637589:
             patch: true
             basedir: '/usr/share/openstack-tripleo-heat-templates/'
             id: '601277'
             command: ''

TLS Everywhere
______________
Setup TLS Everywhere with FreeIPA.

``tls-everywhere``: It will install FreeIPA on first node from freeipa group and it will configure undercloud for TLS Everywhere.
