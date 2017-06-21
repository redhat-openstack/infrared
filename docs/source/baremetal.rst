Baremetal deployment
--------------------

Infrared allows to perform baremetal deployments.

.. note:: Overcloud templates for the deployment should be prepared separately.

1) Undercloud provision step. Foreman plugin will be used in this example.

    infrared foreman -vv \
        -o provision.yml \
        --url foreman.example.com \
        --user foreman_user \
        --password foreman_password \
        --host-address name.of.undercloud.host \
        --host-key /path/to/host/key \
        --role baremetal,undercloud,tester

2) Deploy Undercloud.

    infrared tripleo-undercloud -vv \
        -o undercloud-install.yml \
        --config-file path/to/undercloud.conf \
        --version 11 \
        --build 11 \
        --images-task rpm

3) Deploy Overcloud.

   For InfraRed modification of *instackenv.json* is necessary:
   add *disks* key to *ceph* nodes with list of disks names.


   .. code:: none

     ...
     "cpu": "2",
     "memory": "4096",
     "disk": "0",
     "disks": ["vda", "vdb"],
     "arch": "x86_64",
     ...


    infrared tripleo-overcloud -vv \
        -o overcloud-install.yml \
        --version 11 \
        --instackenv-file path/to/instackenv.json \
        --deployment-files /path/to/the/templates \
        --overcloud-script /path/to/overcloud_deploy.sh \
        --network-protocol ipv4 \
        --network-backend vlan \
        --public-network false \
        --introspect yes \
        --tagging yes \
        --deploy yes \
        --post yes
