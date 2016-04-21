Quickstart
==========

.. note:: This guide assumes:

  * Working on Fedora 23
  * `Virtualenv <setup.html#Virtualenv>`_ is not used.

#. Get `prerequisites <setup.html#prerequisites>`_::

    $ yum install libselinux-python redhat-rpm-config git gcc

#. Clone InfraRed from GitHub::

    $ git clone https://github.com/rhosqeauto/InfraRed.git

#. `Install <setup.html#Install>`_ from source using pip::

    $ cd InfraRed
    $ pip install .
    $ cp ansible.cfg.example ansible.cfg
    $ cp infrared.cfg.example infrared.cfg

#. Generate arguments file for virsh provisioner::

    $ ir-provisioner virsh --generate-conf-file virsh_prov.ini

#. Review the output and edit as needed:

  .. code-block:: ini

    [virsh]
    topology-nodes = 1_undercloud,1_controller,1_compute
    topology-network = default.yml
    host-key = ~/.ssh/id_rsa
    host-user = root
    image = Edit with one of ['sample.yml.example'] options, OR override with CLI: --image=<option>
    host-address = Edit with any value, OR override with CLI: --host-address=<option>

  .. note:: ``image`` and ``host-address`` don't have default values. All arguments can be edited in file or overridden directly from CLI.

#. Execute provisioning. Override file argument if required::

    $ ir-provisioner virsh --image=rhel-7.2.yml --host=my.example.host.redhat.com

 .. note:: In this example, ``image`` doesn't have a valid optional value. You can generate your own file
   based on the provided example file, or you can get it from private repository if available.
