TripleO Undercloud
==================

Deploys a Tripleo undercloud

Setup an Undercloud
-------------------

* ``--version``: Tripleo release to install.
    Accepts either an integer for RHEL-OSP release, or a community release
    name (``Liberty``, ``Mitaka``, ``Newton``, etc...) for RDO release
* ``--build``: Specify a build date or a label for the repositories.
    Examples: ``passed_phase1``, ``2016-08-11.1``
    Not used in case of RDO.

For better fine-tuning of packages, see `custom repositories`_.

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

Add custom repositories to the undercloud, after `installing the Tripleo repositories <Setup Undercloud Packages>`_.

* ``--repos-config`` setup repos using the ansible yum_repository module.
    Using this option enables you to set specific options for each repository:

      .. code-block:: plain
         :caption: repos_config.yml

          ---
          extra_repos:
              - name: my_repo1
                file: my_repo1.file
                description: my repo1
                base_url: http://myurl.com/my_repo1
                enabled: 0
                gpg_check: 0
              - name: my_repo2
                file: my_repo2.file
                description: my repo2
                base_url: http://myurl.com/my_repo2
                enabled: 0
                gpg_check: 0
              ...

      .. note:: This expicitly supports some of the options found in
        yum_repository module (name, file, description, base_url, enabled and gpg_check).
        For more information about this module, visit `Ansible yum_repository documentation <https://docs.ansible.com/ansible/yum_repository_module.html>`_.

* ``repos-urls``: comma separated list of URLs to download repo files to ``/etc/yum.repos.d``

Both options can be used togather::

  infrared tripleo-undercloud [...] --repos-config repos_config.yml --repos-urls "http://yoururl.com/repofile1.repo,http://yoururl.com/repofile2.repo"


Tripleo Undercloud User
-----------------------
``--user-name`` and ``--user-password`` define a user, with password,
for the undercloud. Acorrding to Tripleo guidelines, the default username is ``stack``.
User will be created if necessary.

Overcloud Images
----------------
The final part of the undercloud installation calls for creating the images from which the OverCloud
will be later created.
* Depending on ``--images-task`` these the undercloud can be either:

        * ``build`` images:
                Build the images from a scratch. Use ``--images-url`` to define base image than CentOS.
                For OSP installation, you must provide a url with a valid RHEL image.
        * ``import`` images from url:
                Download pre-built images from ``--images-url``.
        * Download images via ``rpm``:
                Starting from OSP 8, Tripleo is packages with pre-built images avialable via RPM.
                .. note:: This option is invalid for `RDO` installation.

* Use ``--images-repos`` to instruct `infrared` wither to inject the repositories defined in
  the `setup <Setup Undercloud Packages>`_ stage to the image (Allowing later update of the OverCloud)
* Use ``--images-packages`` to define a list of additional packages to install on the OverCloud image
* ``--images-cleanup`` tells `infrared` do remove the images files original after they are uploaded
  to the undercloud's Glance service.

Backup
------
When working on a virtual environment, `infrared` can create a snapshot of the installed undercloud that can be later used
to `restore`_ it on a future run, thus saving installation time.

In order to use this feature, first follow the `Setup an Undercloud`_ section.
Once an undercloud VM is up and ready, run the following::

    ir tripleo-undercloud --quickstart-backup yes

Or optionally, provide the file name of the image to create (defaults to "undercloud-quickstart.qcow2").
.. note:: the filename refers to a path on the hypervisor.

    ir tripleo-undercloud --quickstart-backup yes --quickstart-filename custom-name.qcow2

This will prepare a qcow2 image of your undercloud ready for usage with `Restore`_.

Restore
-------
When working on a virtual environment, `infrared` can use a pre-made undercloud image to quickly set up an environment.
To use this feature, simply run::

    ir tripleo-undercloud --quickstart-restore yes

Or optionally, provide the file name of the image to restore from (defaults to "undercloud-quickstart.qcow2").
.. note:: the filename refers to a path on the hypervisor.

Undercloud Upgrade
---------------------
To upgrade Undercloud to the next major version run the following command::

    infrared tripleo-undercloud -v --upgrade yes

.. note:: Currently, there is upgrade possibility from version 9 to version 10 only.