Beaker
======

Provision baremetal machines using Beaker.

Required arguments
------------------

* ``--url``: URL of the Beaker server.

* ``--password``: The password for the login user.

* ``--host-address``: Address/FQDN of the baremetal machine to be provisioned.


Optional arguments
------------------

* ``--user``: Login username to authenticate to Beaker. (default: admin)

* ``--web-service``: For cases where the Beaker user is not part of the kerberos system,
  there is a need to set the Web service to RPC for authentication rather than rest. (default: rest)

* ``--ca-cert``: For cases where the beaker user is not part of the kerberos system,
  a CA Certificate is required for authentication with the Beaker server.

* ``--host-user``: The username to SSH to the host with. (default: root)

* ``--host-password``: User's SSH password

* ``--host-key``: User's SSH key

* ``--image``: The image to use for nodes provisioning. (Check the "sample.yml.example" under vars/image for example)

* ``--cleanup``: Release the system

.. note:: Please run ``ir beaker --help`` for a full detailed list of all available options.


Execution example
-----------------

Provision::

  ir beaker --url=beaker.server.url --user=beaker.user --password=beaker.password --host-address=host.to.be.provisioned

Cleanup (Used for returning a loaned machine)::

  ir beaker --url=beaker.server.url --user=beaker.user --password=beaker.password --host-address=host.to.be.provisioned --cleanup=yes

