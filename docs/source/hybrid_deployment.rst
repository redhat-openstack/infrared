Hybrid deployment
=================

Infrared allows to deploy hybrid cloud. Hybrid cloud includes virtual nodes and baremetal
nodes.


Create network topology configuration file
------------------------------------------
First the appropriate network configuration should be created.
Most common configuration can include for 3 bridged networks and one nat network for virtual machines
provisioning the following configuration can be used::

    cat << EOF > plugins/virsh/vars/topology/network/3_bridges_1_net.yml
    networks:
        net1:
            name: br-ctlplane
            forward: bridge
            nic: eno2
            ip_address: 192.0.70.200
            netmask: 255.255.255.0
        net2:
            name: br-vlan
            forward: bridge
            nic: enp6s0f0
        net3:
            name: br-link
            forward: bridge
            nic: enp6s0f1
        net4:
            external_connectivity: yes
            name: "management"
            ip_address: "172.16.0.1"
            netmask: "255.255.255.0"
            forward: nat
            dhcp:
                range:
                    start: "172.16.0.2"
                    end: "172.16.0.100"
                subnet_cidr: "172.16.0.0/24"
                subnet_gateway: "172.16.0.1"
            floating_ip:
                start: "172.16.0.101"
                end: "172.16.0.150"

    EOF

.. note:: Change nic names for the bridget networks to match hypervisor interfaces.

.. note:: Make sure you have ``ip_address`` or ``bootproto=dhcp`` defined for the br-ctlplane bridge. This is need to setup ssh access to the nodes after deployment is completed.

Create configurations files for the virtual nodes
-------------------------------------------------

Next step is to add network topology of virtual nodes for the hybrid cloud: ``controller`` and ``undercloud``.
Interface section for every node configuration should match to the network configuration.


Add controller configuration::

    cat << EOF >> plugins/virsh/vars/topology/network/3_bridges_1_net.yml
    nodes:
        undercloud:
            interfaces:
                - network: "br-ctlplane"
                  bridged: yes
                - network: "management"
            external_network:
                network: "management"
    EOF


Add undercloud configuration::

    cat << EOF >> plugins/virsh/vars/topology/network/3_bridges_1_net.yml
        controller:
            interfaces:
                - network: "br-ctlplane"
                  bridged: yes
                - network: "br-vlan"
                  bridged: yes
                - network: "br-link"
                  bridged: yes
                - network: "management"
            external_network:
                network: "management"
    EOF 

Provision virtual nodes with virsh plugin
-----------------------------------------

Once node configurations are done, the ``virsh`` plugin can be used to provision these nodes
on a dedicated hypervisor::

    infrared virsh -v \
        --topology-nodes undercloud:1,controller:1 \
        -e override.controller.memory=28672 \
        -e override.undercloud.memory=28672 \
        -e override.controller.cpu=6 \
        -e override.undercloud.cpu=6 \
        --host-address hypervisor.redhat.com \
        --host-key ~/.ssh/key_file \
        --topology-network 3_bridges_1_net


Install undercloud
------------------
Make sure you provide the undercloud.conf which corresponds
to the baremetal environment::

    infrared tripleo-undercloud -v \
     --version=11 \
     --build=passed_phase1 \
     --images-task=rpm \
     --config-file undercloud_hybrid.conf




Perform introspection and tagging
---------------------------------

Create json file which lists all the baremetal nodes required for deployment::

    cat << EOF > hybrid_nodes.json
    {
       "nodes": [
         {
            "name": "compute-0",
            "pm_addr": "baremetal-mgmt.redhat.com",
            "mac": ["14:02:ec:7c:88:30"],
            "arch": "x86_64",
             "pm_type": "pxe_ipmitool",
            "pm_user": "admin",
            "pm_password": "admin",
            "cpu": "1",
            "memory": "4096",
            "disk": "40"
         }]
    }
    EOF

Run introspection and tagging with infrared::

    infrared tripleo-overcloud -vv -o prepare_instack.yml \
        --version 11 \
        --deployment-files virt  \
        --introspect=yes \
        --tagging=yes \
        --deploy=no \
        -e provison_virsh_network_name=br-ctlplane \
        --hybrid hybrid_nodes.json

.. note:: Make sure to provide the 'provison_virsh_network_name' name to specify
network name to be used for provisioning.

Run deployment with appropriate templates
-----------------------------------------
Copy all the templates to the ``plugins/tripleo-undercloud/vars/deployment/files/hybrid/``
and use ``--deployment-files hybrid``  and ``--deploy yes`` flags to run tripleo-overcloud deployment.
Additionally the ``--overcloud-templates`` option can be used to pass additional templates::

    infrared tripleo-overcloud -vv \
        --version 11 \
        --deployment-files hybrid  \
        --introspect=no \
        --compute-nodes 1 \
        --tagging=no \
        --deploy=yes \
        --overcloud-templates <list of templates>


.. note:: Make sure to provide the ``--compute-nodes 1``  option. It indicates the number of compute nodes to be used for deployment.
