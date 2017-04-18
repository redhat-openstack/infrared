RDO deployment
--------------

Infrared allows to perform RDO based deployments.

To deploy RDO on virtual environment the following steps can be performed.

#. Provision virtual machines on a hypervizor with the virsh plugin. Use CentOS image:

    .. code-block:: bash

        infrared virsh -vv \
            -o provision.yml \
            --topology-nodes undercloud:1,controller:1,compute:1,ceph:1  \
            --host-address my.host.redhat.com \
            --host-key /path/to/host/key \
            --image-url https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2 \
            -e override.controller.cpu=8 \
            -e override.controller.memory=32768

    .. note:: The ``-e override.controller.*`` construction is used here to add more memory and cpu's to the VM's which are required by the specific product installation.

#. Install the undercloud. Use RDO release name as a version:

    .. code-block:: bash

        infrared tripleo-undercloud -vv -o install.yml \
            -o undercloud-install.yml \
            --version ocata

#. ``import`` overcloud images from `<https://images.rdoproject.org>`_ or ``build`` them locally (see the `ovecrloud images <tripleo-undercloud.html#overcloud-images>`_ page for details):

    .. code-block:: bash

        # import images
        infrared tripleo-undercloud -vv \
            -o undercloud-images.yml \
            --images-task=import \
            --images-url=https://images.rdoproject.org/ocata/rdo_trunk/current-tripleo/stable/

        # or build images
        infrared tripleo-undercloud -vv \
            -o undercloud-images.yml \
            --images-task=build \

    .. note:: Overcloud image build process usually takes more time (up to 1 hour) than import.

#. Install RDO:

    .. code-block:: bash

        infrared tripleo-overcloud -v \
            -o overcloud-install.yml \
            --version ocata \
            --deployment-files virt \
            --introspect yes \
            --tagging yes \
            --deploy yes \
            --post yes
