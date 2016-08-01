.. highlight:: plain

Advanced features
=================

Breakpoints
^^^^^^^^^^^

Advanced usage sometimes requires partial execution of the ospd playbook. This can be achieved with
`Ansible tags <http://docs.ansible.com/ansible/playbooks_tags.html>`_

Use `InfraRed` with ``--dry-run`` flag. Instead of executing ansible, this will only generate the required ansible input::

    ir-installer [...] ospd [...] --dry-run -o OUTPUT_FILE

Ansible will take the `yaml` file ``OUTPUT_FILE`` as ``--extra-vars`` input file.

List the available tags of the `ospd` playbooks::

    ansible-playbook -i hosts --extra-vars @OUTPUT_FILE playbooks/install.yml  --list-tags

Execute only the desired tags. For example, this will only install the undercloud and stop::

    ansible-playbook -i hosts --extra-vars @OUTPUT_FILE playbooks/install.yml --tags=undercloud


OverCloud Image Update
^^^^^^^^^^^^^^^^^^^^^^

OSPD creates the OverCloud nodes from a virtual machine image. InfraRed updates that image's packages
to match RH-OSP core bits ``build``. To avoid that and keep the OverCloud image as created,
set ``update_overcloud_core_bits`` to ``False``::

  ir-installer [...] ospd [...] --extra-vars update_overcloud_core_bits=False

Custom repositories
^^^^^^^^^^^^^^^^^^^

Infrared allows to add custom repositories to the UnderCloud when you're running `OSPD`, after installing the default repositories of the `OSPD` release.
This can be done passing through ``--extra-vars`` with the following key:
    * ``ospd.extra_repos.from_url`` which will download a repo file to ``/etc/yum.repos.d``
..    * ospd.extra_repos.from_config which will setup a repo using the ansible yum_repository module

.. .. note:: Since both options hold a list, you must create a yaml file in both cases to pass in the extra-vars option.

#. Using ``ospd.extra_repos.from_url``:

    Create a yaml file:

    .. code-block:: yaml
       :caption: repos.yml

        ---
        ospd:
           extra_repos:
               from_url:
                   - http://yoururl.com/repofile1.repo
                   - http://yoururl.com/repofile2.repo

    Run ir-installer::

        ir-installer --extra-vars=@repos.yml ospd

..
  TODO(acruz): uncomment this when ansible 2.1 be shipped with yum_repository module
  #. Using ospd.extra_repos.from_config

      Using this option enables you to set specific options for each repository:

      .. code-block:: plain
         :caption: repos.yml

          ---
          ospd:
             extra_repos:
                 from_config:
                     - { name: my_repo1, file: my_repo1.file, description: my repo1, base_url: http://myurl.com/my_repo1, enabled: 0, gpg_check: 0 }
                     - { name: my_repo2, file: my_repo2.file, description: my repo2, base_url: http://myurl.com/my_repo2, enabled: 0, gpg_check: 0 }
          ...

      .. note:: As you can see, ospd.extra_repos.explicity support some of the options found in yum_repository module (name, file, description, base_url, enabled and gpg_check). For more information about this module, visit `Ansible yum_repository documentation <https://docs.ansible.com/ansible/yum_repository_module.html>`_.

      Run ir-installer::

          ir-installer -e @repos.yml ospd


Custom/local tempest tester
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You might have a specific version of tempest to test locally in a particular directory, and you want to use it.
Infrared allows you to use this instead of the default git repository. To do so, all you need to do is pass the key tester.local_dir as extra-vars to ir-tester:

Run ir-tester::

    ir-tester tempest --extra-vars tester.local_dir-/patch/for/your/tempest


Scalability
^^^^^^^^^^^

Infrared allows to perform scale tests on different services.

Currently supported services for tests:
    * compute
    * ceph-storage
    * swift-storage

#. To scale compute service:

    Deployment should have at least 3 compute nodes.

    Run ansible playbook::

        ansible-playbook -vvvv -i hosts -e @install.yml playbooks/installer/ospd/post_install/scale_compute.yml

    It will scale compute nodes down to 1 and after that scale compute node back to 3.

#. To scale ceph-storage service:

    Deployment should have at least 3 ceph-storage nodes.

    Run ansible playbook::

        ansible-playbook -vvvv -i hosts -e @install.yml playbooks/installer/ospd/post_install/ceph_compute.yml

    It will scale compute nodes down to 1 and after that scale compute node back to 3.

#. To scale swift-storage service:

    Deployment should have at least 3 swift-storage nodes.

    Run ansible playbook::

            ansible-playbook -vvvv -i hosts -e @install.yml playbooks/installer/ospd/post_install/swift_compute.yml

    .. note:: Swift has a parameter called ``min_part_hours`` which configures amount of time that should be passed between two rebalance processes. In real production environment this parameter is used to reduce network load. During the deployment of swift cluster for further scale testing we set it to 0 to decrease amount of time for scale.
