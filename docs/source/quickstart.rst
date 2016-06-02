Quickstart
==========
.. note:: This guide assumes:

  * `Virtualenv <setup.html#Virtualenv>`_ is used
  * `Prerequisites <setup.html#prerequisites>`_ are set-up
  * We strongly urge to read `Setup <setup.html#Setup>`_ instructions for known issues and workarounds before you proceed

* Clone InfraRed from GitHub::

    git clone https://github.com/rhosqeauto/InfraRed.git

.. note::

  * For production, `Stable branch <https://github.com/rhosqeauto/InfraRed/tree/stable>`_ is probably good point to start with:

    git clone https://github.com/rhosqeauto/InfraRed.git -b stable

* `Install <setup.html#Install>`_ from source using pip::

    cd InfraRed
    pip install --upgrade pip
    pip install .
    cp ansible.cfg.example ansible.cfg
    cp infrared.cfg.example infrared.cfg

* Generate arguments file for virsh provisioner::

    ir-provisioner virsh --generate-conf-file virsh_prov.ini

* Review the config file and edit as required:

  .. code-block:: ini

    [virsh]
    topology-nodes = undercloud:1,controller:1,compute:1
    topology-network = default.yml
    host-key = ~/.ssh/id_rsa
    host-user = root
    image = Edit with one of ['sample.yml.example'] options, OR override with CLI: --image=<option>
    host-address = Edit with any value, OR override with CLI: --host-address=<option>

  .. note:: ``image`` and ``host-address`` don't have default values. All arguments can be edited in file or overridden directly from CLI.


* In previous example, ``image`` doesn't have a valid optional value. You can generate your own file based on the provided example file we provide, or you can get it from private repository if available:

  .. code-block:: ini

   cat settings/provisioner/virsh/image/sample.yml.example
   ---
   file: "Fedora-Cloud-Base-23-20151030.x86_64.qcow2"
   server: "http://mirror.pnl.gov/fedora/linux/releases/23/Cloud/x86_64/Images/"

* Prepare sample file with your image:

  .. code-block:: ini

   mv settings/provisioner/virsh/image/sample.yml.example \
   settings/provisioner/virsh/image/fedora23.yml

* Execute provisioning using prepared image. Override arguments if needed::

    ir-provisioner virsh --image=fedora23.yml --host-address=my.host.com

