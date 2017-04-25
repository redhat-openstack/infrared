Configuration
=============

`Infrared` configuration is stored in special directory, called ``.infrared``.

`Infrared` looks for configuration directory in working path (``./.infrared/``),
if not found it will look in the user's home (``~/.infrared``).
When non of those is found, `infrared` will create a new configuration directory
in or in user's home.

.. note:: Users can override configuration dir location using environment variable
  ``INFRARED_CONF_DIR``. In this case directory will be automatically created too.

Configuration directory holds ``infrared.cfg`` which controls the location of:

* ``workspaces_base_folder``: the workspaces base directory
* ``plugins_conf_file``: path to ``plugins.ini`` file

By default, both are placed inside ``.infrared/``. To change that replace the default file with your own and edit it::

    cp infrared.cfg.example ./.infrared/infrared.cfg
