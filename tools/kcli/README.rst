========================
kcli - Khaleesi CLI tool
========================

``kcli`` is intended to reduce Khaleesi users' dependency on external CLI tools.

Setup
=====

.. note:: On Fedora 23 `BZ#1103566 <https://bugzilla.redhat.com/show_bug.cgi?id=1103566>`_
 calls for::

  $ dnf install redhat-rpm-config

Use pip to install from source::

  $ pip install tools/kcli

.. note:: For development work it's better to install in editable mode::

  $ pip install -e tools/kcli

Conf
====

.. note:: Assumes that ``kcli`` is installed, else follow Setup_.

``kcli`` will look for ``kcli.cfg`` in the following order:

#. In working directory: ``./kcli.cfg``
#. In user home directory: ``~/.kcli.cfg``
#. In system settings: ``/etc/khaleesi/kcli.cfg``

.. note:: To specify a different directory or different filename, override the
 lookup order with ``KCLI_CONFIG`` environment variable::

    $ KCLI_CONFIG=/my/config/file.ini kcli --help

Running kcli
============

.. note:: Assumes that ``kcli`` is installed, else follow Setup_.

You can get general usage information with the ``--help`` option::

  kcli --help

This displays options you can pass to ``kcli``.

.. note:: Some setting files are hard-coded to look for the ``$WORKSPACE``
 environment variable (see `Khaleesi - Cookbook`) that should point to the
 directory where ``khaleesi`` and ``khaleesi-settings`` have been cloned. You
 can define it manually to work around that::

  $ export WORKSAPCE=$(dirname `pwd`)

Extra-Vars
----------
One can set/overwrite settings in the output file using the '-e/--extra-vars'
option. There are 2 ways of doing so:

1. specific settings: (key=value form)
    --extra-vars provisioner.site.user=a_user
2. path to a settings file: (starts with '@')
    --extra-vars @path/to/a/settings_file.yml

The '-e/--extra-vars' can be used more than once.

Merging order
-------------
Except options based on the settings dir structure, kcli accepts input of
predefined settings files (with -n/--input) and user defined specific options
(-e/--extra-vars).
The merging priority order listed below:

1. Input files
2. Settings dir based options
3. Extra Vars
