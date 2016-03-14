This is a placeholder for the new provisioner to hold the topology files
in the form of:

nodes:
    # Dict of nodes
    example:
        name: controller
        amount: 1
        cpu: "{{ !lookup provisioner.virsh.image.cpu }}"
        memory: 8192
        os: &os
            type: linux
            variant: "{{ !lookup provisioner.virsh.image.os.variant }}"
        disk: &disk
            size: "{{ !lookup provisioner.virsh.image.disk.size }}"
            dev: /dev/vda
            path: /var/lib/libvirt/images
        network: &network_params
            interfaces: &interfaces
                management: &mgmt_interface
                    label: eth0
                data: &data_interface
                    label: eth1
                external: &external_interface
                    label: eth2
        groups:
            - controller
            - openstack_nodes


