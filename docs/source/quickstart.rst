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
2) Arguments file

1. CLI
~~~~~~
In order to know which are the mandatory parameters the user should provide, please run::

    ir-provisioner --help

Notice that the only two mandatory paramters in `virsh` provisioner are the '--host-address' & '--host-key'.
We can now execute the provisioning process by providing those parameters through the CLI::

    ir-provisioner --host-address=my.host.address --host-key=~/.ssh/id_rsa

BOOM! That how easy it is ;-)

2. Arguments file
~~~~~~~~~~~~~~~~~
An arguments file is an INI based configuration file which has the needed values for tools execution.
It been easily created and it shows all options needed for basic execution in more readable way. The user will then need to review the file and to take care of the missing values in the relevant section (`virsh` in our case) in this file.

Generate arguments file for virsh provisioner::

    ir-provisioner virsh --generate-conf-file virsh_prov.ini

Review the config file and edit as required:

.. code-block:: plain
   :emphasize-lines: 6,7
   :caption: virsh_prov.ini

   [virsh]
   topology-nodes = undercloud:1,controller:1,compute:1
   topology-network = default.yml
   host-user = root
   host-key = Required argument. Edit with any value, OR override with CLI: --host-key=<option>
   host-address = Required argument. Edit with any value, OR override with CLI: --host-address=<option>

In this example, we can easily notice that we need to replace the values if 'host-key' & 'host-address'::

    sed -e 's/host-key = .*/host-key = ~\/.ssh\/id_rsa/g' -i virsh_prov.ini
    sed -e 's/host-address = .*/host-address = my.host.address/g' -i virsh_prov.ini

.. note:: ``host-key`` and ``host-address`` don't have default values. All arguments can be edited in file or overridden directly from CLI.
.. warning:: Users without access to redhat internal network will have to provide a url to a guest image using the "--image-url" option

Execute provisioning using the newly created and modified arguments file::

    ir-provisioner virsh --from-file=virsh_prov.ini

Done. Quick & Easy!

For `installer` and `tester` stages continue to `Using InfraRed <execute.html>`_



