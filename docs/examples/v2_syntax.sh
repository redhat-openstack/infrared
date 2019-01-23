## CLEANUP ##
infrared virsh -v -o cleanup.yml \
    --host-address example.redhat.com \
    --host-key ~/.ssh/id_rsa \
    --kill yes

## PROVISION ##
infrared virsh -v \
    --topology-nodes undercloud:1,controller:1,compute:1 \
    --host-address example.redhat.com \
    --host-key ~/.ssh/id_rsa \
    --image-url http://www.images.com/rhel-7.qcow2

## UNDERCLOUD ##
infrared tripleo-undercloud -v mirror tlv \
    --version 9 \
    --build passed_phase1 \
    --ssl true \
    --images-task rpm

## OVERCLOUD ##
infrared tripleo-overcloud -v \
    --version 10 \
    --introspect yes \
    --tagging yes \
    --deploy yes \
    --deployment-files virt \
    --network-backend vxlan \
    --overcloud-ssl false \
    --network-protocol ipv4

## POST TASKS ##
infrared cloud-config -v \
    -o cloud-config.yml \
    --deployment-files virt \
    --tasks create_external_network,forward_overcloud_dashboard,network_time,tempest_deployer_input

## TEMPEST ##
infrared tempest -v \
    --config-options "image.http_image=http://www.images.com/cirros.qcow2" \
    --openstack-installer tripleo \
    --openstack-version 9 \
    --tests sanity

# Fetch inventory from active workspace
WORKSPACE=$(ir workspace list | awk '/*/ {print $2}')
ansible -i .workspaces/$WORKSPACE/hosts all -m ping
