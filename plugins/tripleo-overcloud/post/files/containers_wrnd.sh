#!/bin/bash
source /home/stack/stackrc
#w/a for bz 1457358
for i in `nova list|awk '/compute/ {print $(NF-1)}'|awk -F"=" '{print $NF}'`; do echo $i; ssh -o StrictHostKeyChecking=no heat-admin@$i "sudo ovs-vsctl add-br br-ex; sudo docker restart neutron_ovs_agent"; done

#w/a for bz 1464212
for i in `nova list|awk '/compute/ {print $(NF-1)}'|awk -F"=" '{print $NF}'`; do echo $i; ssh -o StrictHostKeyChecking=no heat-admin@$i "sudo test -d /var/lib/config-data/nova_libvirt/etc/libvirt/secrets || sudo mkdir /var/lib/config-data/nova_libvirt/etc/libvirt/secrets"; done

#w/a for bz 1459592
TAG1=$(ssh -o StrictHostKeyChecking=no heat-admin@`nova list|awk '/compute/ {print $(NF-1)}'|awk -F"=" '{print $NF}'|head -n1` "sudo docker ps"|awk '/openstack-nova-libvirt-docker/ {print $2}')
echo $TAG1
cat >> Dockerfile << EOF
FROM $TAG1
RUN yum localinstall -y https://mprivozn.fedorapeople.org/openstack2/libvirt-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-interface-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-config-network-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-nwfilter-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-libs-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-3.5.0-1.el7.x86_64.rpm  https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-qemu-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-secret-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-lxc-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-network-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-kvm-3.5.0-1.el7.x86_64.rpm  https://mprivozn.fedorapeople.org/openstack2/libvirt-client-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-nodedev-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-mpath-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-iscsi-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-config-nwfilter-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-core-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-disk-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-scsi-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-core-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-gluster-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-logical-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-rbd-3.5.0-1.el7.x86_64.rpm
EOF



for i in `nova list|awk '/compute/ {print $(NF-1)}'|awk -F"=" '{print $NF}'`; do echo $i; ssh -o StrictHostKeyChecking=no heat-admin@$i "sudo mkdir /root/1459592"; scp -o StrictHostKeyChecking=no Dockerfile heat-admin@$i:/tmp/; ssh -o StrictHostKeyChecking=no heat-admin@$i "sudo mv /tmp/Dockerfile /root/1459592; sudo docker build -t openstack-nova-libvirt-docker /root/1459592; sudo docker tag openstack-nova-libvirt-docker $TAG1"; done


for i in `nova list|awk '/compute/ {print $(NF-1)}'|awk -F"=" '{print $NF}'`; do echo $i; ssh -o StrictHostKeyChecking=no heat-admin@$i "curl -o tool.py http://git.openstack.org/cgit/openstack/tripleo-heat-templates/plain/docker/docker-toool; sudo python /home/heat-admin/tool.py -c nova_libvirt|tail -n1|tee /tmp/runcommand; sudo sed -i 's/nova_libvirt /nova_libvirt -d /' /tmp/runcommand; sudo docker rm -f nova_libvirt; sudo bash /tmp/runcommand"; done


# w/a for bz 1464182
for i in `nova list|awk '/compute/ {print $(NF-1)}'|awk -F"=" '{print $NF}'`; do echo $i; ssh -o StrictHostKeyChecking=no -tt heat-admin@$i "sudo docker exec -u root -it nova_compute bash -c 'echo 270d5597e0414f018ba9787924d7626b|tee /etc/machine-id'"; done

