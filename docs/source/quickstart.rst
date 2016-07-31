.. highlight:: plain

Quickstart
==========

.. note:: This guide assumes:

  * Latest version of `Python 2 <https://www.python.org/downloads/>`_ installed
  * `Virtualenv <setup.html#Virtualenv>`_ is used
  * `Prerequisites <setup.html#prerequisites>`_ are set-up
  * We strongly urge to read all `Setup <setup.html#Setup>`_ instructions first
  * Quickstart is assuming you are use Fedora as main distro for deployment and provisioning (RHEL needs private adjustments)

Clone InfraRed stable from GitHub::

    git clone https://github.com/rhosqeauto/InfraRed.git -b stable

.. note:: This is documentation for stable version. Check in top left corner of this page if your stable branch tag matches version of documentation. If not true, `let us know <contacts.html#contact-us>`_!

`Install <setup.html#Install>`_ from source using pip::

    cd InfraRed
    pip install --upgrade pip setuptools
    pip install .
    cp ansible.cfg.example ansible.cfg

Basic Usage Example
===================
Provisioning
------------

In this example we'll use `virsh` provisioner in order to demonstrate how easy and fast it is to provision machines using InfraRed.
For basic execution, the user should only provide data for the mandatory parameters, this can be done by two ways:

1) CLI
2) INI File

1. CLI
~~~~~~
In order to know which are the mandatory parameters (for `virsh`) the user should provide, please run::

    ir-provisioner virsh --help

Notice that the only three mandatory paramters in `virsh` provisioner are the 'host-address', 'host-key' & 'topology-nodes'.
We can now execute the provisioning process by providing those parameters through the CLI::

    ir-provisioner virsh --host-address=my.host.address --host-key=~/.ssh/id_rsa --topology-nodes="undercloud:1,controller:1,compute:1"

..  note:: The value of the topology-nodes option is a comma-separated string in a "type:amount" format. Please check the settings/topology dir for a complete list of the available types. (In the example above, three nodes will be provisioned: 1 undercloud, 1 controller & 1 compute)

BOOM! That how easy it is ;-)

2. INI File
~~~~~~~~~~~
Unlike with CLI, here a new configuration file (INI based) will be created.
This file contains all the default & mandatory parameters in a section of its own (named 'virsh' in our case), so the user can easily replace all mandatory parameters.
When the file is ready, it should be provided as an input for the '--from-file' option.

Generate INI file for `virsh` provisioner::

    ir-provisioner virsh --generate-conf-file virsh_prov.ini

Review the config file and edit as required:

.. code-block:: plain
   :emphasize-lines: 6,7
   :caption: virsh_prov.ini

   [virsh]
   host-key = Required argument. Edit with any value, OR override with CLI: --host-key=<option>
   host-address = Required argument. Edit with any value, OR override with CLI: --host-address=<option>
   topology-nodes = Required argument. Edit with one of the allowed values OR override with CLI: --topology-nodes=<option>
   topology-network = default.yml
   host-user = root


.. note:: ``host-key``, ``host-address`` and ``topology-nodes`` don't have default values. All arguments can be edited in file or overridden directly from CLI.

Edit mandatory parameters values::

    sed -e 's/host-key .*/host-key = ~\/.ssh\/id_rsa/g' -i virsh_prov.ini
    sed -e 's/host-address .*/host-address = my.host.address/g' -i virsh_prov.ini

Execute provisioning using the newly created INI file::

    ir-provisioner virsh --from-file=virsh_prov.ini --topology-nodes="undercloud:1,controller:1,compute:1"

Done. Quick & Easy!

.. warning:: Users without access to redhat internal network will have to provide a url to a guest image using the "--image-url" option

For `installer` and `tester` stages continue to `Using InfraRed <execute.html>`_



