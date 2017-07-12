#!/bin/bash
set -x
TAG1=$(docker ps|awk '/openstack-nova-libvirt-docker/ {print $2}')
echo $TAG1
mkdir -p /root/1459592
cat > /root/1459592/Dockerfile <<EOF
FROM ${TAG1}
RUN yum localinstall -y https://mprivozn.fedorapeople.org/openstack2/libvirt-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-interface-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-config-network-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-nwfilter-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-libs-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-3.5.0-1.el7.x86_64.rpm  https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-qemu-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-secret-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-lxc-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-network-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-kvm-3.5.0-1.el7.x86_64.rpm  https://mprivozn.fedorapeople.org/openstack2/libvirt-client-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-nodedev-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-mpath-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-iscsi-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-config-nwfilter-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-core-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-disk-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-scsi-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-core-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-gluster-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-logical-3.5.0-1.el7.x86_64.rpm https://mprivozn.fedorapeople.org/openstack2/libvirt-daemon-driver-storage-rbd-3.5.0-1.el7.x86_64.rpm
EOF
cat /root/1459592/Dockerfile

docker build -t openstack-nova-libvirt-docker /root/1459592
docker tag openstack-nova-libvirt-docker $TAG1

curl -o tool.py http://git.openstack.org/cgit/openstack/tripleo-heat-templates/plain/docker/docker-toool
python /home/heat-admin/tool.py -c nova_libvirt|tail -n1|tee /tmp/runcommand
sed -i 's/nova_libvirt /nova_libvirt -d /' /tmp/runcommand
sed -i 's#/etc/libvirt/:ro#/etc/libvirt/#' /tmp/runcommand
docker rm -f nova_libvirt
bash /tmp/runcommand
