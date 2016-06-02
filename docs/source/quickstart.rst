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

.. note:: This is documentation for stable version. Check in top left corner of this page if you stable branch tag matches version of documentation. If not true, let us know!

`Install <setup.html#Install>`_ from source using pip::

    cd InfraRed
    pip install --upgrade pip
    pip install .
    cp ansible.cfg.example ansible.cfg
    cp infrared.cfg.example infrared.cfg

Generate arguments file for virsh provisioner::

    ir-provisioner virsh --generate-conf-file virsh_prov.ini

Review the config file and edit as required:

.. code-block:: plain
   :emphasize-lines: 6,7
   :caption: virsh_prov.ini

   [virsh]
   topology-nodes = undercloud:1,controller:1,compute:1
   topology-network = default.yml
   host-key = ~/.ssh/id_rsa
   host-user = root
   image = Edit with one of ['sample.yml.example'] options, OR override with CLI: --image=<option>
   host-address = Edit with any value, OR override with CLI: --host-address=<option>

.. note:: ``image`` and ``host-address`` don't have default values. All arguments can be edited in file or overridden directly from CLI.


In previous example, ``image`` doesn't have a valid optional value. You can generate your own file based on the provided example file we provide, or you can get it from private repository if available:

.. code-block:: plain
   :caption: settings/provisioner/virsh/image/sample.yml.example

   ---
   file: "Fedora-Cloud-Base-23-20151030.x86_64.qcow2"
   server: "http://mirror.pnl.gov/fedora/linux/releases/23/Cloud/x86_64/Images/"

Prepare sample file with required information about image used for provisioning::

   mv settings/provisioner/virsh/image/sample.yml.example \
   settings/provisioner/virsh/image/fedora23.yml

Execute provisioning. Override arguments if needed::

    ir-provisioner virsh --image=fedora23.yml --host-address=my.host.com

For `installer` and `tester` stages continue to `Using InfraRed <execute.html>`_



