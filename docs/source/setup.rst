Setup
=====

Supported distros
-----------------
Currently supported distros are:

* Fedora 22, 23
* RHEL 7.2

Prerequisites
-------------
.. note:: **Sudo or root access is needed to install prerequisities!**

General requirements::

  sudo dnf/yum install git gcc libffi-devel openssl-devel

Virtualenv_ is required::

  sudo dnf/yum install python-virtualenv

Ansible requires `python binding for SELinux <http://docs.ansible.com/ansible/intro_installation.html#managed-node-requirements>`_::

  sudo dnf/yum install libselinux-python

otherwise it won't be able to run modules with copy/file/template functions!

.. note:: libselinux-python is in `Prerequisites`_ but doesn't have a pip package. It must be installed on system level.
.. note:: Ansible requires also **libselinux-python** installed on all nodes using copy/file/template functions!

Virtualenv
----------

InfraRed shares many dependencies with other OpenStack products and projects. Therefore there's a high probability of conflicts with python dependencies, which would result either with InfraRed failure, or worse, with breaking dependencies for other OpenStack products.
When working from source, it is recommended to use python `virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_ to avoid corrupting the system packages::

  virtualenv .venv
  source .venv/bin/activate

.. warning:: **It is mandatory that latest pip is used!**

   .. code-block:: ini

      pip install --upgrade pip

.. note:: On Fedora 23 with EPEL enabled, `BZ#1103566 <https://bugzilla.redhat.com/show_bug.cgi?id=1103566>`_ also requires:

   .. code-block:: ini

      dnf install redhat-rpm-config

Installation
------------

Install from source after cloning repo from GitHub::

  cd InfraRed
  pip install .

.. note::
   For development work it's better to install in editable mode

   .. code-block:: ini

      pip install -e .

Configuration
-------------

InfraRed will look for ``infrared.cfg`` in the following order:

#. In working directory: ``./infrared.cfg``
#. In user home directory: ``~/.infrared.cfg``
#. In system settings: ``/etc/infrared/infrared.cfg``

Set up `ansible config <http://docs.ansible.com/ansible/intro_configuration.html>`_ if it was not configured already::

  cp ansible.cfg.example ansible.cfg

Additional settings
^^^^^^^^^^^^^^^^^^^
In InfraRed configuration file, you can adjust where ansible looks for directories and entry/cleanup playbooks::

    InfraRed configuration file
    # ===========================

    [defaults]
    settings  = settings
    modules   = library
    roles     = roles
    playbooks = playbooks

    [provisioner]
    main_playbook = provision.yml
    cleanup_playbook = cleanup.yml

    [installer]
    main_playbook = install.yml
    cleanup_playbook = cleanup.yml

    [tester]
    main_playbook = test.yml
    cleanup_playbook = cleanup.yml

Private settings
-------------------

Infrared allows user to define several folders to store settings and spec files. This can be used, for example, to store public and private settings separately. To define additional settings folders edit the ``settings`` option in the Infrared configuration file::

    [defaults]
    settings  = settings:private_settings
    ...

.. note:: InfraRed tool must be tied to infrastructure at certain level, therefore requires part of configuration not shared publicly. It is assumed this part will be located in private settings.
