Configuration
=============

Infrared uses the IR_HOME environment variable which points where infrared
should keep all the internal configuration files and workspaces.

By default the ``IR_HOME`` points to ``~/.infrared`` in user home
directory. If it does not exist a new one will be created.

To change that default location user can simply set ``IR_HOME``, for example::

    $ IR_HOME=/tmp/newhome ir workspace list


This will generate default configurations files in the specified directory.


Defaults from environment variables
-----------------------------------

Infrared will load all environment variables starting with ``IR_`` and will
transform them in default argument values that are passed to all modules.

This means that ``IR_FOO_BAR=1`` will do the same thing as adding
``--foo-bar=1`` to infrared CLI.

Infrared uses the same precedence order as Ansible when it decide
which value to load, first found is used:

* command line argument
* environment variable
* configuration file
* code (plugin spec default) value


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
