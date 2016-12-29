TripelO
=======

TripelO installer installs a Tripleo UnderCloud

Product
-------

* ``--product-version``: Openstack release to install.
    Accepts either an integer for RHEL-OSP release, or a community release
    name (``Liberty``, ``Juno``, ``Newton``, etc...) for RDO release
* ``--product-build``: Specify a build date for the repositories
* ``--product-director-build``: Specify a different build for `director` repositories.
    Only for releases 7-9 where `director` is packaged separately.

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

Add custom repositories to the UnderCloud, after installing the default `product`_ repositories.

.. .. note:: Since both options hold a list, you must create a yaml file in both cases to pass in the extra-vars option.

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

  infrared tripleo [...] --repos-config repos_config.yml --repos-urls "http://yoururl.com/repofile1.repo,http://yoururl.com/repofile2.repo"

