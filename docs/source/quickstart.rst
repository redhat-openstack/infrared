.. include:: warning.txt

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

.. warning:: While most topologies will work 'out of the box', some topologies (like external ceph, netapp, etc) requires internal credentials which we cannot upload upstream. Users with access to redhat internal network can run the following command to download a file contains some credentials & other sensitive data, other user will have to provide this data explicitly everywhere there is a reference to private variables.

  .. code-block:: text

    wget --no-check-certificate https://url.corp.redhat.com/infrared-private -O infrared-private.yml

Basic Usage Example
"""""""""""""""""""
Provisioning
------------

In this example we'll use `virsh <execute.html#virsh>`_ provisioner in order to demonstrate how easy and fast it is to provision machines using InfraRed.
For basic execution, the user should only provide data for the mandatory parameters, this can be done by two ways:

1) `CLI`_
2) `INI File`_

CLI
~~~
To list all parameters (for `virsh`) and their description, run::

    ir-provisioner virsh --help

Notice that the only three mandatory paramters in `virsh` provisioner are:

  * ``--host-address`` - the host IP or FQDN to ssh to
  * ``--host-key`` - the private key file used to authenticate to your ``host-address`` server
  * ``--topology-nodes`` - type and role of nodes you would like to deploy (e.g: controller:3 == 3 VMs that will act as controllers)

We can now execute the provisioning process by providing those parameters through the CLI::

    ir-provisioner virsh --host-address=$HOST --host-key=$HOST_KEY --topology-nodes="undercloud:1,controller:1,compute:1" -e @infrared-private.yml

..  note:: The value of the topology-nodes option is a comma-separated string in a "type:amount" format. Please check the settings/topology dir for a complete list of the available types. (In the example above, three nodes will be provisioned: 1 undercloud, 1 controller & 1 compute)

That is it, the machines are now provisioned and accessible.

.. note:: You can also use the auto-generated ssh config file to easily access the machines

  .. code-block:: text

    ssh -F ansible.ssh.config controller-0

INI File
~~~~~~~~
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

.. note:: Do not use double quotes or apostrophes for the string values
    in the configuration ini file. Infrared will NOT remove those quotation marks
    that surround the values.

Edit mandatory parameters values in the INI file::

   [virsh]
   host-key = ~/.ssh/id_rsa
   host-address = my.host.address
   topology-nodes = undercloud:1,controller:1,compute:1
   topology-network = default.yml
   host-user = root

Execute provisioning using the newly created INI file::

    ir-provisioner virsh --from-file=virsh_prov.ini -e @infrared-private.yml

.. note:: You can always overwrite parameters from INI file with parameters from CLI

  .. code-block:: text

    ir-provisioner virsh --from-file=virsh_prov.ini --topology-nodes="undercloud:1,controller:1,compute:1,ceph:1" -e @infrared-private.yml

Done. Quick & Easy!

.. warning:: Users without access to redhat internal network will have to provide a url to a guest image using the "--image-url" option

Installing
----------

Now let's demonstrate the installation process by deploy an OpenStack environment using redhat OSPD (OpenStack Director) on the nodes we have provisioned in the previous stage (The deployment in this case will be 'virthost' type, see how to `setup Virthost machine`_).

Just like in the provisioning stage, here also the user should take care of the mandatory parameters (by CLI or INI file) in order to be able to start the installation process. Lets provide the mandatory parameter (``deployment-files``) and choose to work with RHOS version 8, this time using the CLI only::

  ir-installer ospd --deployment-files=$PWD/settings/installer/ospd/deployment/virt --product-version=8 --product-core-version=8 -e @infrared-private.yml

.. note:: Please notice that the ``deployment-file`` parameters requires a full path of the deployment files dir.

Done.

.. _setup Virthost machine: setup.html#virthost-machine

OSPD Quickstart
---------------

InfraRed provides a quick solution to deploy OSPD with a pre-configured undercloud from latest build for testing/POC.

1. Provision: No undercloud node should be provisioned in the provisioning stage.

.. code-block:: text

  ir-provisioner virsh --host-address=$HOST --host-key=$HOST_KEY --topology-nodes="controller:1,compute:1" -e @infrared-private.yml

2. Install: InfraRed will notice that no UC is provided and will build one from a snapshot of an installed UC from latest available build.

.. code-block:: text

  ir-installer ospd --deployment-files=$PWD/settings/installer/ospd/deployment/virt --product-version=9 --product-core-version=9 -e @infrared-private.yml


For detailed information on the usage of the various installers, provisioners & tester continue to `Using InfraRed <execute.html>`_
