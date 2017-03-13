## CLEANUP ##
ir-provisioner -d virsh -v \
  --topology-nodes=undercloud:1,controller:1,compute:1 \
  --host-address=example.redhat.com \
  --host-key=~/.ssh/id_rsa \
  --image-url=www.images.com/rhel-7.qcow2 \
  --cleanup

## PROVISION ##
ir-provisioner -d virsh -v \
  --topology-nodes=undercloud:1,controller:1,compute:1 \
  --host-address=example.redhat.com \
  --host-key=~/.ssh/id_rsa \
  --image-url=http://www.images.com/rhel-7.qcow2

## OSPD ##
ir-installer --debug mirror tlv ospd -v -o install.yml\
  --product-version=9 \
  --product-build=latest \
  --product-core-build=passed_phase1 \
  --undercloud-ssl=true \
  --images-task=rpm \
  --deployment-files=$PWD/settings/installer/ospd/deployment/virt \
  --network-backend=vxlan \
  --overcloud-ssl=false \
  --network-protocol=ipv4

ansible-playbook -i hosts -e @install.yml \
  playbooks/installer/ospd/post_install/create_tempest_deployer_input_file.yml

## TEMPEST ##
ir-tester --debug tempest -v \
  --config-options="image.http_image=http://www.images.com/cirros.qcow2" \
  --tests=sanity.yml

ansible -i hosts all -m ping
