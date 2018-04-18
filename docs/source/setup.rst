.. include:: warning.txt

.. highlight:: plain

Setup
=====

Supported distros
-----------------
Currently supported distros are:

* Fedora 22, 23
* RHEL 7.2 (best effort only, deprecated)
* RHEL 7.3

.. warning:: Python 2.7 and virtualenv are required.

Prerequisites
-------------
.. warning:: Sudo or root access is needed to install prerequisities!

General requirements::

  sudo dnf/yum install git gcc libffi-devel openssl-devel sshpass

.. note:: Dependencies explained:

   * git - version control of this project

   * gcc - used for compilation of C backends for various libraries

   * libffi-devel - required by `cffi <http://cffi.readthedocs.io/en/latest/>`_

   * openssl-devel - required by `cryptography <http://cryptography.readthedocs.io/en/latest/>`_

   * sshpass - required by wait_for ansible module

Closed Virtualenv_ is required to create clean python environment separated from system::

  sudo dnf/yum install python-virtualenv

Ansible requires `python binding for SELinux <http://docs.ansible.com/ansible/intro_installation.html#managed-node-requirements>`_::

  sudo dnf/yum install libselinux-python

otherwise it won't be able to run modules with copy/file/template functions!

.. note:: libselinux-python is in `Prerequisites`_ but doesn't have a pip package. It must be installed on system level.
.. warning:: Ansible requires also **libselinux-python** installed on all nodes using copy/file/template functions. Without this step all such tasks will fail!

Virtualenv
----------

InfraRed shares many dependencies with other OpenStack products and projects. Therefore there's a high probability of conflicts with python dependencies, which would result either with InfraRed failure, or worse, with breaking dependencies for other OpenStack products.
When working from source, it is recommended to use python `virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_ to avoid corrupting the system packages::

  virtualenv .venv
  source .venv/bin/activate

.. warning:: **It is mandatory that latest pip is used (especially in when working with RHEL)!**

   .. code-block:: ini

      pip install --upgrade pip setuptools

.. note:: On Fedora 23 with EPEL repository enabled, `RHBZ#1103566 <https://bugzilla.redhat.com/show_bug.cgi?id=1103566>`_ also requires:

   .. code-block:: ini

      dnf install redhat-rpm-config

Installation
------------
Clone stable branch from Github repository::

  git clone https://github.com/rhosqeauto/InfraRed.git -b stable


Install InfraRed from source::

  cd InfraRed
  pip install .

.. note::
   For development work it's better to install in editable mode and work with master branch

   .. code-block:: ini

      git checkout master
      pip install -e .

Configuration
-------------

.. note:: InfraRed only requires explicit configuraion file when non-default values are used.

InfraRed will look for ``infrared.cfg`` in the following order:

#. Environment variable: ``$IR_CONFIG=/my/config/infrared.cfg``
#. In working directory: ``./infrared.cfg``
#. In user home directory: ``~/.infrared.cfg``
#. In system settings: ``/etc/infrared/infrared.cfg``

*If no configuration file is supplied, InfraRed will load default values as listed in ``infrared.cfg.example*


Set up `ansible config <http://docs.ansible.com/ansible/intro_configuration.html>`_ if it was not configured already::

  cp ansible.cfg.example ansible.cfg

Additional settings
^^^^^^^^^^^^^^^^^^^
In InfraRed configuration file, you can adjust where ansible looks for directories and entry/cleanup playbooks:

.. code-block:: plain
   :caption: infrared.cfg.example

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
----------------

Infrared allows user to define several folders to store settings and spec files. This can be used, for example, to store public and private settings separately. To define additional settings folders edit the ``settings`` option in the Infrared configuration file::

    [defaults]
    settings  = settings:private_settings
    ...

.. note:: InfraRed tool must be tied to infrastructure at certain level, therefore requires part of configuration not shared publicly. It is assumed this part will be located in private settings.

For more questions please `contact us <contacts.html#contact-us>`_.

.. _virthost:
Virthost machine
----------------

Virthost machine is the target machine where InfraRed's virsh provisioner will create
virtual machines and networks (using libvirt) to emulate baremetal infrastructure.

As such there are few specific requirements it has to meet.

Generally, It needs to have **enough memory and disk** storage to hold multiple decent VMs
(each with GBytes of RAM and dozens of GB of disk).
Also for acceptable responsiveness (speed of deployment/testing) just <4 threads or low GHz
CPU is not a recommended choice  (if you have old and weaker CPU than current mid-high end mobile
phone CPU you may suffer performance wise - and so more timeouts during deployment or in tests).


Especially, for Ironic (TripleO) to control them, those **libvirt VMs** need to be bootable/controllable
for **iPXE provisioning**.
And also extra user has to exist, which can ssh in the virthost and control (restart...) libvirt VMs.

.. note:: InfraRed is currently attempting to configure or validate all (most) of this but it's scattered across all provisiner/installer steps.
          Due to nature of installers such as OSPd and current InfraRed structure it may not be 100% safe for rerunning
          (failure in previous run may prevent following one from succeeding in these preparation steps).
          We are currently working on a more idempotent approach which should resolve the above issues (if present).

What **user has to provide**:

    - have machine with **sudoer user ssh access** and **enough resources**,
      as minimum requirements for one VM are:

      + VCPU: 2|4|8
      + RAM: 8|16
      + HDD: 40GB+
      + in practice disk may be smaller, as they are thin provisioned,
        as long as you don't force writing all the data (aka Tempest with rhel-guest instead of cirros etc)

    - tested is just **RHEL-7.3** as OS, with also **CentOS** expected to work

      + may work with other distributions (best-effort/limited support)

    - **yum repositories** has to be **preconfigured** by user (foreman/...) before using InfraRed so it can install dependencies

      + esp. for InfraRed to handle ``ipxe-roms-qemu`` it requires either **RHEL-7.3-server channel**,
        or (deprecated) *RHEL-7.2 with OSP<10 channels* (10+ is 7.3)

What **InfraRed takes care of**:

    - ``ipxe-roms-qemu`` package of at least ``version 2016xxyy`` needs to be installed

    - other basic packages installed

      + ``libvirt``, ``libguestfs{-tools,-xfs}``, ``qemu-kvm``, ``wget``, ``virt-install``
      + ``virt-manager``, ``xorg-x11-apps``, ``xauth``, ``virt-viewer`` possibly for debugging (or multiple ssh tunnels can be used)

    - **virtualization support** (VT-x/AMD-V)

      + ideally with **nested=1** support

    - ``stack`` user created with polkit privileges for *org.libvirt.unix.manage*
    - **ssh key** with which InfraRed can authenticate (created and) added for *root* and *stack* user,
      atm they are handled differently/separately:

      + for *root* the ``infared/id_rsa.pub`` gets added to authorized_keys
      + for *stack* ``infrared/id_rsa_undercloud.pub`` is added to authorized_keys, created/added later during installation
