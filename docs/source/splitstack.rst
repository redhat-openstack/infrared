SplitStack deployment
---------------------

Infrared allows to perform SplitStack_ based deployment.

.. _SplitStack: https://access.redhat.com/documentation/en-us/red_hat_openstack_platform/11/html/director_installation_and_usage/chap-configuring_basic_overcloud_requirements_on_pre_provisioned_nodes

To deploy SplitStack on virtual environment the following steps can be performed.

1) Provision virtual machines on a hypervisor with the virsh plugin.::

	infrared virsh -o provision.yml \
		--topology-nodes undercloud:1,controller:3,compute:1 \
		--topology-network split_nets \
		--host-address $host \
		--host-key $key \
		--host-memory-overcommit False \
		--image-url http://cool_iamge_url \
		-e override.undercloud.disks.disk1.size=55G \
		-e override.controller.cpu=8 \
		-e override.controller.memory=32768 \
		-e override.controller.deploy_os=true \
		-e override.compute.deploy_os=true

2) Install the undercloud using required version(currently 11 and 12 was tested)::

	infrared tripleo-undercloud -o install.yml \
		-o undercloud-install.yml \
		--mirror tlv \
		--version 12 \
		--build passed_phase1 \
		--splitstack yes \
		--ssl yes

3) Install overcloud::

	infrared tripleo-overcloud -o overcloud-install.yml \
		--version 12 \
		--deployment-files splitstack \
		--role-files default \
		--deploy yes \
		--splitstack yes \
		--post no
