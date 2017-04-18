RDO deployment
--------------

Infrared allows to perform RDO based deployments.

To deploy RDO on virtual environment the following steps can be performed.

1) Provision virtual machines on a hypervizor with the virsh plugin. Use CentOS image::

    infrared virsh -vv \
        -o provision.yml \
        --topology-nodes undercloud:1,controller:1,compute:1,ceph:1  \
        --host-address my.host.redhat.com \
        --host-key /path/to/host/key \
        --image-url https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2 \
        -e override.controller.cpu=8 \
        -e override.controller.memory=32768

2) Install the undercloud. Use RDO release name as a version::

    infrared tripleo-undercloud -vv -o install.yml \
        -o undercloud-install.yml \
        --version ocata

3) Build or import overcloud images from `<https://images.rdoproject.org>`_:: 

    # import images
    infrared tripleo-undercloud -vv \
        -o undercloud-images.yml \
        --images-task=import \
        --images-url=https://images.rdoproject.org/ocata/rdo_trunk/current-tripleo/stable/

    # or build images
    infrared tripleo-undercloud -vv \
        -o undercloud-images.yml \
        --images-task=build \

.. note:: Overcloud image build process usually takes more time than import.

4) Install RDO::

     infrared tripleo-overcloud -v \
         -o overcloud-install.yml \
         --version ocata \
         --deployment-files virt \
         --introspect yes \
         --tagging yes \
         --deploy yes \
         --post yes
