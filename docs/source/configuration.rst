Configuration
=============

`infrared` configuration is stored in special directory.

By default `infrared` looks for `./.infrared` and if it's absent - `~/.infrared`
While `./.infrared` should be created by user `~/.infrared`, in opposit, will be create
automaticaly, if not exists.

In addition, configuration direcrory can be set by environment variable `INFRARED_CONF_DIR`
In this case directory will be automaticaly created too.

In configuration diractory placed such important infrared items, as:

* ``workspace base directory``: directory, where workspaces and their content are placed
* ``plugins.ini file``: plugins configuration and references
* ``infrared.cfg`` (optional): ``infrared`` configuration file


`infrared.cfg` allows to change default options such as:

* ``workspaces_base_folder``: the workspaces base directory
* ``plugins_conf_file``: path to `plugins.ini` file

This can be done by creating a configuration file, ``infrared.cfg`` in `infrared` configuration directory,
and overriding default values in it::

    cp infrared.cfg.example infrared.cfg


When ``infrared.cfg`` file is not found, default options will be used:

.. literalinclude:: ../../infrared.cfg.example
   :language: ini
