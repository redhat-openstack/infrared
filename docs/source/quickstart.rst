QuickStart
==========

Setup
-----

Clone InfraRed 2.0 from GitHub::

    git clone https://github.com/rhos-infra/InfraRed.git -b IR2

`Install <setup.html#Install>`_ from source using pip::

    cd InfraRed
    pip install --upgrade pip setuptools
    pip install .

You must have an active `profile <profile.html#profile>`_ to work. This profile will manage your environment details::

    infrared profile create quickstart
    infrared profile activate quickstart

Provision
---------

In this example we'll use `virsh <execute.html#virsh>`_ provisioner in order to demonstrate how easy and fast it is to provision machines using `InfraRed`.

Add the virsh `plugin <plugin.html>`_::

    infrared plugin add plugins/virsh

Print `virsh` help message and all input options::

    infrared virsh --help

For basic execution, the user should only provide data for the mandatory parameters, this can be done in two ways:

1) `CLI`_
2) `Answers File`_

CLI
^^^

Notice the only three mandatory paramters in `virsh` provisioner are:

  * ``--host-address`` - the host IP or FQDN to ssh to
  * ``--host-key`` - the private key file used to authenticate to your ``host-address`` server
  * ``--topology-nodes`` - type and role of nodes you would like to deploy (e.g: ``controller=3`` == 3 VMs that will act as controllers)

We can now execute the provisioning process by providing those parameters through the CLI::

    infrared virsh --host-address $HOST --host-key $HOST_KEY --topology-nodes "undercloud=1;controller=1;compute=1"

That is it, the machines are now provisioned and accessible::

    TASK [update inventory file symlink] *******************************************
                         [[ previous task time: 0:00:00.306717 = 0.31s / 209.71s ]]
    changed: [localhost]

    PLAY RECAP *********************************************************************
    compute-0                  : ok=4    changed=3    unreachable=0    failed=0
    controller-0               : ok=5    changed=4    unreachable=0    failed=0
    localhost                  : ok=4    changed=3    unreachable=0    failed=0
    undercloud-0               : ok=4    changed=3    unreachable=0    failed=0
    virthost                   : ok=85   changed=29   unreachable=0    failed=0

                         [[ previous task time: 0:00:00.237104 = 0.24s / 209.94s ]]
                         [[ previous play time: 0:00:00.555806 = 0.56s / 209.94s ]]
                   [[ previous playbook time: 0:03:29.943926 = 209.94s / 209.94s ]]
                        [[ previous total time: 0:03:29.944113 = 209.94s / 0.00s ]]

.. note:: You can also use the auto-generated ssh config file to easily access the machines

Answers File
^^^^^^^^^^^^

Unlike with `CLI`_, here a new answers file (INI based) will be created.
This file contains all the default & mandatory parameters in a section of its own (named ``virsh`` in our case), so the user can easily replace all mandatory parameters.
When the file is ready, it should be provided as an input for the ``--from-file`` option.

Generate Answers file for `virsh` provisioner::

    infrared virsh --generate-answers-file virsh_prov.ini

Review the config file and edit as required:

.. code-block:: plain
   :emphasize-lines: 6,7
   :caption: virsh_prov.ini

   [virsh]
   host-key = Required argument. Edit with any value, OR override with CLI: --host-key=<option>
   host-address = Required argument. Edit with any value, OR override with CLI: --host-address=<option>
   topology-nodes = Required argument. Edit with one of the allowed values OR override with CLI: --topology-nodes=<option>
   host-user = root

.. note:: ``host-key``, ``host-address`` and ``topology-nodes`` don't have default values. All arguments can be edited in file or overridden directly from CLI.

.. note:: Do not use double quotes or apostrophes for the string values
    in the answers file. `InfraRed` will NOT remove those quotation marks
    that surround the values.

Edit mandatory parameters values in the answers file::

   [virsh]
   host-key = ~/.ssh/id_rsa
   host-address = my.host.address
   topology-nodes = undercloud=1;controller=1;compute=1
   host-user = root

Execute provisioning using the newly created answers file::

    infrared virsh --from-file=virsh_prov.ini

.. note:: You can always overwrite parameters from answers file with parameters from CLI::

  .. code-block:: text

    infrared virsh --from-file=virsh_prov.ini --topology-nodes="undercloud=1;controller=1;compute=1;ceph=1"

Done. Quick & Easy!
