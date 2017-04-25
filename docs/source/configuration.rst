Configuration
=============

`infrared` allows to change default options such as:

* ``workspaces_base_folder``: the workspaces base folder
* ``plugins_conf_file``: the plugins configuration file path

This can be done by creating a configuration file, ``./infrared.cfg``, and overriding default values in it::

    cp infrared.cfg.example infrared.cfg


When ``infrared.cfg`` file is not found, default options defined in ``infrared.cfg.example`` file will be used:

.. literalinclude:: ../../infrared.cfg.example
   :language: ini
