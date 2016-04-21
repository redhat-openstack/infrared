Setup
=====

Prerequisites
-------------

Ansible `requires python binding for SELinux <http://docs.ansible.com/ansible/intro_installation.html#managed-node-requirements>`_::

  $ dnf install libselinux-python

.. note:: On Fedora 23 `BZ#1103566 <https://bugzilla.redhat.com/show_bug.cgi?id=1103566>`_
 calls for::

  $ dnf install redhat-rpm-config

Virtualenv
----------

InfraRed shares many dependencies with other OpenStack products and projects. Therefore there's a high probability of
conflicts with python dependencies, which would result either with InfraRed failure, or worse, with breaking dependencies
for other OpenStack products.
When working from source, it is recommended to use python `virutalenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_
to avoid corrupting the system packages::

  $ virtualenv --system-site-packages .venv
  $ source .venv/bin/activate

`Get python binding for SELinux <https://dmsimard.com/2016/01/08/selinux-python-virtualenv-chroot-and-ansible-dont-play-nice/>`_::

  $ cp -rv /usr/lib64/python2.7/site-packages/selinux/ $VIRTUAL_ENV/lib/python2.7/site-packages


.. note:: libselinux-python is in `Prerequisites`_ but doesn't have a pip package. Create virtualenv with site packages enabled to avoid this hack::

  $ virtualenv --system-site-packages .venv

Install
-------

Install from source after cloning repo from GitHub::

 $ cd Infrared
 $ pip install .

.. note:: For development work it's better to install in editable mode::

  $ pip install -e .

Configure
---------

``infrared`` will look for ``infrared.cfg`` in the following order:

#. In working directory: ``./infrared.cfg``
#. In user home directory: ``~/.infrared.cfg``
#. In system settings: ``/etc/infrared/infrared.cfg``

Create a quick cfg file from example file:

  $ cp infrared.cfg.example infrared.cfg

To specify a different directory or different filename, override the
lookup order with ``IR_CONFIG`` environment variable::

  $ IR_CONFIG=/my/config/file.ini ir-provision --help

