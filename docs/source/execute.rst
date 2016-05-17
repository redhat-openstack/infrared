.. note:: This section is incomplete

Running InfraRed
================

InfraRed has several "entry points". Currently available: [``ir-provisioner``, ``ir-installer``]

You can get general usage information with the ``--help`` option::

  ir-provisioner --help

This displays options you can pass to ``ir-provision``, as well as plugins available as "subcommands"::

  $ ir-provision --help
    usage: ir-provisioner [-h] [-v] [--inventory INVENTORY] [-d]
                          {foreman,virsh,openstack,beaker} ...

    positional arguments:
      {foreman,virsh,openstack,beaker}
        foreman             Provision systems using 'Foreman'
        virsh               Provision systems using virsh
        openstack           Provision systems using Ansible OpenStack modules
        beaker              Provision systems using Beaker

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Control Ansible verbosity level
      --inventory INVENTORY
                            Inventory file
      -d, --debug           Run InfraRed in DEBUG mode

