Configuration
=============

Infrared configuration is stored in special directory, called ``.infrared``.

Infrared looks for configuration directory in working path (``./.infrared/``) and then in user's home directory (``~/.infrared/``).
If none is found, a default one will be created in user's home directory.

Users can override configuration dir path using environment variable `INFRARED_CONF_DIR`
In this case directory will be automaticaly created too.

Configuration directory holds ``infrared.cfg`` which controls the location of:

* ``workspaces_base_folder``: the workspaces base directory
* ``plugins_conf_file``: path to `plugins.ini` file

By default, both are placed inside ``.infrared/``. To chagne that replace the default file with your own and edit it::

    cp infrared.cfg.example ./.infrared/infrared.cfg

