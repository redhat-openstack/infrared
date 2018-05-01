Configuration
=============

Infrared uses the IR_HOME environment variable which points where infrared
should keep all the internal configuration files and workspaces.

Currently by default the ``IR_HOME`` points the current working directory
from which the infrared command is run.

To change that default location user can simply set ``IR_HOME``, for example::

    $ IR_HOME=/tmp/newhome ir workspace list


This will generate default configurations files in the specified directory.

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
