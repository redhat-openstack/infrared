Configuration
=============

`Infrared` configuration is stored in special directory, called ``.infrared``.

`Infrared` looks for configuration directory in working path (``./.infrared/``),
if not found it will look in the user's home (``~/.infrared``).
When non of those is found, `infrared` will create a new configuration directory in user's home dir.

.. note:: Users can override configuration dir location using environment variable
  ``INFRARED_CONF_DIR``. In this case directory will be automatically created too.

Configuration directory holds ``infrared.cfg`` which controls the location of:

* ``workspaces_base_folder``: the workspaces base directory
* ``plugins_conf_file``: path to ``plugins.ini`` file

By default, both are placed inside ``.infrared/``. To change that replace the default file with your own and edit it::

    cp infrared.cfg.example ./.infrared/infrared.cfg


Ansible configuration and limitations
-------------------------------------
Usually `infrared` does not touch the settings specified in the ansible configuration
file (``ansible.cfg``), with few exceptions.

Internally `infrared` use few Ansible environment variable to set the directories
for common resources (callback plugins, filter plugins, roles, etc); this means
that the following keys from the Ansible configuration files are ignored:

* ``callback_plugins``
* ``filter_plugins``
* ``roles_path``

It is still possible to defined custom paths for those items setting the corresponding
environment variables:

* ``ANSIBLE_CALLBACK_PLUGINS``
* ``ANSIBLE_FILTER_PLUGINS``
* ``ANSIBLE_ROLES_PATH``
