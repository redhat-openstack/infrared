.. highlight:: plain

Setup
=====

Supported distros
-----------------
Currently supported distros are:

* Fedora 22, 23, 24, 25
* RHEL 7.2 (best effort, deprecated)
* RHEL 7.3
* RHEL 7.4

.. warning:: Python 2.7 and virtualenv are required.

Prerequisites
-------------
.. warning:: sudo or root access is needed to install prerequisites!

General requirements::

  sudo yum install git gcc libffi-devel openssl-devel

.. note:: Dependencies explained:

   * git - version control of this project

   * gcc - used for compilation of C backends for various libraries

   * libffi-devel - required by `cffi <http://cffi.readthedocs.io/en/latest/>`_

   * openssl-devel - required by `cryptography <http://cryptography.readthedocs.io/en/latest/>`_

Closed Virtualenv_ is required to create clean python environment separated from system::

  sudo yum install python-virtualenv

Ansible requires `python binding for SELinux <http://docs.ansible.com/ansible/intro_installation.html#managed-node-requirements>`_::

  sudo yum install libselinux-python

otherwise it won't be able to run modules with copy/file/template functions!

.. note:: libselinux-python is in `Prerequisites`_ but doesn't have a pip package. It must be installed on system level.
.. note:: Ansible requires also **libselinux-python** installed on all nodes using copy/file/template functions. Without this step all such tasks will fail!

Virtualenv
----------

``infrared`` shares dependencies with other OpenStack products and projects.
Therefore there's a high probability of conflicts with python dependencies,
which would result either with ``infrared`` failure, or worse, with breaking dependencies
for other OpenStack products.
When working from source,
`virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_ usage
is recommended for avoiding corrupting of system packages::

  virtualenv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install --upgrade setuptools

.. warning:: **Use of latest ``pip`` is mandatory, especially on RHEL platform!**

.. note:: On Fedora 23 with EPEL repository enabled,
    `RHBZ#1103566 <https://bugzilla.redhat.com/show_bug.cgi?id=1103566>`_ also requires
    ::

        dnf install redhat-rpm-config

Installation
------------
Clone stable branch from Github repository::

  git clone https://github.com/redhat-openstack/infrared.git

Install ``infrared`` from source::

  cd infrared
  pip install .

.. note:: For development work it's better to install in editable
    mode and work with master branch::

      pip install -e .

Bash completion
---------------
Bash completion script is in etc/bash_completion.d directory of git repository.
To enable global completion copy this script to proper path in the system (/etc/bash_completion.d)::

  cp etc/bash_completion.d/infrared /etc/bash_completion.d/

Alternatively, just source it to enable completion temporarily::

  source etc/bash_completion.d/infrared

When working in virtualenv, might be a good idea to add import of this script to the
virtualenv activation one::

  echo ". $(pwd)/etc/bash_completion/infrared" >> ${VIRTUAL_ENV}/bin/activate

