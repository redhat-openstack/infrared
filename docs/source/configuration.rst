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


Ansible configuration and limitations
-------------------------------------
Usually `infrared` does not touch the settings specified in the ansible configuration
file (``ansible.cfg``), with few exceptions.

Internally `infrared` use Ansible environment variables to set the directories
for common resources (callback plugins, filter plugins, roles, etc); this means
that the following keys from the Ansible configuration files are ignored:

* ``callback_plugins``
* ``filter_plugins``
* ``roles_path``

It is possible to define custom paths for those items setting the corresponding
environment variables:

* ``ANSIBLE_CALLBACK_PLUGINS``
* ``ANSIBLE_FILTER_PLUGINS``
* ``ANSIBLE_ROLES_PATH``
