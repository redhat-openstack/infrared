Configuration
=============

InfraRed 2.0 allows to change default options such as:

* Profiles base folder (``profiles_base_folder``).
* Plugins configuration file (``plugins_conf_file``).

This can be done by creating configuration file (./infrared.cfg) and overriding default values in that file::

    cp infrared.cfg.example infrared.cfg


When infrared.cfg file is not provided the InfraRed 2.0 will use the default configuration:

.. code-block:: plain

   profiles_base_folder: '.profiles',
   plugins_conf_file: '.plugins.ini'
