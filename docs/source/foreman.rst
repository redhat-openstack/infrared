Foreman
=======

Provision baremetal machine using Foreman and add it to the inventory file.

Required arguments
------------------

* ``--url``: The Foreman API URL.

* ``--user``: Foreman server login user.

* ``--password``: Password for login user

* ``--host-address``: Name or ID of the target host as listed in the Foreman server.


Optional arguments
------------------

* ``--strategy``: Whether to use Foreman or system ``ipmi`` command. (default: foreman)

* ``--action``: Which command to send with the power-management selected by mgmt_strategy. (default: cycle)

* ``--wait``: Whether wait for host to return from rebuild or not. (default: yes)

* ``--host-user``: The username to SSH to the host with. (default: root)

* ``--host-password``: User's SSH password

* ``--host-key``: User's SSH key

* ``--host-ipmi-username``: Host IPMI username.

* ``--host-ipmi-password``: Host IPMI password.

* ``--roles``: Host roles

* ``--os-id``: An integer represents the operating system ID to set

* ``--medium-id``: An integer represents the medium ID to set

.. note:: Please run ``ir foreman --help`` for a full detailed list of all available options.


Execution example
-----------------

::

  ir foreman --url=foreman.server.api.url --user=foreman.user --password=foreman.password --host-address=host.to.be.provisioned
