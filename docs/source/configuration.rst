Configuration
=============

InfraRed 2.0 allows to change default options such as:

* ``profiles_base_folder``: the profiles base folder
* ``plugins_conf_file``: the plugins configuration file path

This can be done by creating configuration file (./infrared.cfg) and overriding default values in it::

    cp infrared.cfg.example infrared.cfg


When infrared.cfg file is not provided the InfraRed 2.0 will use the default options defined in the infrared.cfg.example file: 

.. literalinclude:: ../../infrared.cfg.example
   :language: ini
