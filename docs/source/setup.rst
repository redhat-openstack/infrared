Setup
=====

.. note:: On Fedora 23 `BZ#1103566 <https://bugzilla.redhat.com/show_bug.cgi?id=1103566>`_
 calls for::

  $ dnf install redhat-rpm-config

Install
^^^^^^^

Use pip to install from source::

  $ pip install <path_to_infrared_dir>

So, After cloning repo from GitHub::

 $ cd Infrared
 $ pip install .

.. note:: For development work it's better to install in editable mode::

  $ pip install -e .

Configure
^^^^^^^^^

``infrared`` will look for ``infrared.cfg`` in the following order:

#. In working directory: ``./infrared.cfg``
#. In user home directory: ``~/.infrared.cfg``
#. In system settings: ``/etc/infrared/infrared.cfg``

If the configuration file ``infrared.cfg`` doesn't exist in any of
the locations above, the InfraRed project's dir will be used as the default
location for configurations.

To specify a different directory or different filename, override the
lookup order with ``IR_CONFIG`` environment variable::

$ IR_CONFIG=/my/config/file.ini ir-provision --help

