TripelO
=======

TripelO installer installs a Tripleo UnderCloud

Setup Tripleo Packages
----------------------

* ``--version``: Openstack release to install.
    Accepts either an integer for RHEL-OSP release, or a community release
    name (``Liberty``, ``Juno``, ``Newton``, etc...) for RDO release
* ``--build``: Specify a build date for the repositories

For better fine-tuning of packages, see `custom repositories`_.

Undercloud Configuration
------------------------

TripleO configure the undercloud according to ``undercloud.conf`` file.
Use ``--config-file`` to provide this file, or let `InfraRed` generate one automatically,
and use ``--config-options`` to provide a list of ``section.option=value`` that will override
specific fields in it.

Use ``--ssl`` option to deteramain whether to activate UnderCloud SSL or not.
If true, a self-signed SSL cert will be generated.

Custom Repositories
-------------------

Add custom repositories to the UnderCloud, after `installing the Tripleo repositories <setup Tripleo packages>`_.

* ``--repos-config`` Setup repos using the ansible yum_repository module.
    Using this option enables you to set specific options for each repository:

      .. code-block:: plain
         :caption: repos_config.yml

          ---
          extra_repos:
              - name: my_repo1
                file: my_repo1.file
                description: my repo1
                base_url: http://myurl.com/my_repo1
                enabled: 0, gpg_check: 0
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


Tripleo User
------------
Setup (if missing) a user (with password) for Tripleo. Acorrding to Tripleo guidelines, the default
username is ``stack``.

Overcloud Images
----------------
The final part of the UnderCloud installation calls for creating the images from which the OverCloud
will be later created.
* Depending on ``--images-task`` these the UnderCloud can be either:

        * ``build`` images:
                Build the images from a scratch. Use ``--images-url`` to define base image than CentOS.
                For OSP installation, you must provide a url with a valid RHEL image.
        * ``import`` images from url:
                Download pre-built images from ``--images-url``.
        * Download images via ``rpm``:
                Starting from OSP 8, Tripleo is packages with pre-built images avialable via RPM.
                .. note:: This option is invalid for `RDO` installation.

* Use ``--images-repos`` to instruct `InfraRed` wither to inject the repositories defined in
  the `setup <Setup Tripleo Packages>`_ stage to the image (Allowing later update of the OverCloud)
* Use ``--images-packages`` to define a list of additional packages to install on the OverCloud image
* ``--images-cleanup`` tells `InfraRed` do remove the images files original after they are uploaded
 to th UnderCloud's Glance service.

Backup
------
Working on a virtual environment, `InfraRed` can create a snapshot of the installed UnderCloud
that can be later used to `restore`_ it on a future run, thus saving installation time.

Restore
-------
Skip the above process and use a `backup`_ snapshot image of the undercloud.

