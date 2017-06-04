#!/bin/bash
##################################################################
# octavia-post-deploy.sh
# Performs additional configuration steps to be run after the
# overcloud has been deployed. This comfiguration will be
# incorporated in the Octavia deployment support in future
# releases.

# NOTE: this is not very composable-role-friendly and needs modification if
# octavia services are not hosted on the same nodes as the neutron API server.

# Temporarily use the undercloud environment to get the list of controllers.
# Note that the relevant hostnames are related to the role and is dependent on
# the deployment. By default, the Octavia services are currently on nodes
# hosting the 'controller' role.
source ~stack/stackrc

CONTROLLERS=`nova list --fields name,networks | grep controller     | \
    awk -e '{ split($6, net, "="); printf "%s.localdomain=%s\n", $4, net[2] }'`


# The rest of the operations are performed in the overcloud. It may
# be necessary to modify the name of shell environment file if running
# multiple overclouds.
source ~stack/overcloudrc

# This creates a heat template that automates some of the steps:
#
# * create an ssh key to allow enabling ssh communication to the
#   amphorae
# * create neutron network resources in the overcloud for
#   communication between the amphorae and the Octavia services
# * create the nova flavor for the amphorae
#
cat > octavia-post.yaml << EOF
heat_template_version: ocata

description: >
    This template performs Octavia specific configuration on the overcloud.

parameters:
  OctaviaSSHKeyName:
    type: string
    description: name of the SSH key to register with Nova
    default: 'octavia-ssh-key'
  OctaviaSSHKeyPath:
    type: string
    description: local path to the key file
    default: ''
  OctaviaNetworkName:
    type: string
    description: name of load balancer network used by Octavia
    default: 'lb-mgmt-net'
  OctaviaSubnetName:
    type: string
    description: name of the load balancer subnet used by Octavia
    default: 'lb-mgmt-subnet'
  OctaviaSubnetCIDR:
    type: string
    description: Network address for load balancer network used by Octavia
    default: '192.168.199.0/24'
  OctaviaGateway:
    type: string
    description: Gateway address for load balancer network
    default: '192.168.199.1'
  OctaviaPoolStart:
    type: string
    description: First address in the subnet allocation pool.
    default: '192.168.199.50'
  OctaviaPoolEnd:
    type: string
    description: Last address in the subnet allocation pool.
    default: '192.168.199.200'
  OctaviaFlavorId:
    type: number
    description: Openstack Flavor id for the LB appliances
    default: 65
  OctaviaFlavorName:
    type: string
    description: Name for Openstack flavor for LB appliances
    default: m1.amphora
  OctaviaFlavorDisk:
    type: number
    default: 3
  OctaviaFlavorRam:
    type: number
    default: 1024
  OctaviaFlavorCPUs:
    type: number
    default: 1
  OctaviaSecurityGroupName:
    type: string
    default: lb-mgmt-sec-grp


resources:

  OctaviaFlavor:
    type: OS::Nova::Flavor
    properties:
      name: {get_param: OctaviaFlavorName}
      flavorid: {get_param: OctaviaFlavorId}
      disk: {get_param: OctaviaFlavorDisk}
      ram: {get_param: OctaviaFlavorRam}
      vcpus: {get_param: OctaviaFlavorCPUs}


# Is it possible to make this so that the user has
# to provide the key-file?
#
  OctaviaSSHKey:
    type: OS::Nova::KeyPair
    properties:
      save_private_key: true
      name: {get_param: OctaviaSSHKeyName}

  OctaviaLBNetwork:
    type: OS::Neutron::Net
    properties:
      name: {get_param: OctaviaNetworkName}

  OctaviaSubnet:
    type: OS::Neutron::Subnet
    properties:
      cidr: {get_param: OctaviaSubnetCIDR}
      name: {get_param: OctaviaSubnetName}
      network_id: {get_resource: OctaviaLBNetwork}
      gateway_ip: {get_param: OctaviaGateway}
      allocation_pools:
        - start: {get_param: OctaviaPoolStart}
          end: {get_param: OctaviaPoolEnd}

  OctaviaSecurityGroup:
    type: OS::Neutron::SecurityGroup
    properties:
      name: {get_param: OctaviaSecurityGroupName}
      rules:
        - protocol: tcp
          port_range_min: 22
          port_range_max: 22
        - protocol: tcp
          port_range_min: 9443
          port_range_max: 9443

outputs:
  public_key:
    description: Octavia public key
    value: {get_attr: [OctaviaSSHKey, public_key]}
  private_key:
    description: Octavia private key
    value: {get_attr: [OctaviaSSHKey, private_key]}
  octavia_network_id:
    description: network id for LB network
    value: {get_resource: OctaviaLBNetwork}
  octavia_flavor:
    description: amphora flavor specs
    value: {get_attr: [OctaviaFlavor, show]}
  octavia_sec_group:
    description: amphora security group
    value: {get_resource: OctaviaSecurityGroup}
EOF

openstack stack create --template octavia-post.yaml octavia-post

# Once the stack is created, we can obtain the private and public key and other
# info from the stack outputs.
openstack stack show -f json -c outputs octavia-post  > outputs.json
cat outputs.json | \
    jq -r  '.["outputs"] | .[] | select(.output_key == "private_key")| .["output_value"]' \
    > octavia_ssh_key
cat outputs.json | \
    jq -r  '.["outputs"] | .[] | select(.output_key == "public_key")| .["output_value"]' \
    > octavia_ssh_key.pub
LB_NETWORK_ID=`cat outputs.json | \
    jq -r  '.["outputs"] | .[] | select(.output_key == "octavia_network_id")| .["output_value"]'`
LB_SECGROUP_ID=`cat outputs.json | \
    jq -r  '.["outputs"] | .[] | select(.output_key == "octavia_sec_group")| .["output_value"]'`

# Iterate through the host/IP element and perform post deployment steps. We
# will build a list of IPs based on the health manager ports created in the
# loop and use them to configure the controller_ip_port_list later.
CONTROLLER_IP_LIST=
for rec in $CONTROLLERS;
do
    rec_array=(${rec//=/ })
    node_hostname=${rec_array[0]}
    node=${rec_array[1]}

    # Distribute SSH keys and certs to each controller node.
    ssh -o StrictHostKeyChecking=no -q heat-admin@$node 'sudo mkdir -p /etc/octavia/.ssh'
    ssh -o StrictHostKeyChecking=no heat-admin@$node 'sudo mkdir -p /etc/octavia/certs/private'

    cat octavia_ssh_key | ssh -o StrictHostKeyChecking=no heat-admin@$node 'sudo bash -c "cat > /etc/octavia/.ssh/octavia_ssh_key"'
    cat octavia_ssh_key.pub | ssh -o StrictHostKeyChecking=no heat-admin@$node 'sudo bash -c "cat > /etc/octavia/.ssh/octavia_ssh_key.pub"'

    cat client.pem | ssh -o StrictHostKeyChecking=no heat-admin@$node 'sudo bash -c "cat > /etc/octavia/certs/client.pem"'
    cat ca_01.pem | ssh -o StrictHostKeyChecking=no heat-admin@$node 'sudo bash -c "cat > /etc/octavia/certs/ca_01.pem"'
    cat private/cakey.pem | ssh -o StrictHostKeyChecking=no heat-admin@$node 'sudo bash -c "cat > /etc/octavia/certs/private/cakey.pem"'

    # Make sure permissions are correct!
    ssh -o StrictHostKeyChecking=no heat-admin@$node 'sudo chown -R octavia:octavia /etc/octavia/.ssh/*'
    ssh -o StrictHostKeyChecking=no heat-admin@$node 'sudo chown -R octavia:octavia /etc/octavia/certs/*'

    # Create a neutron port on the load balancer management network on each
    # controller node for the health managers.
    port_id_and_mac=$(neutron port-create --name octavia-health-manager-$node_hostname-listen-port \
        --binding:host_id=$node_hostname --security-group lb-mgmt-sec-grp \
        --device-owner Octavia:health-mgr \
        lb-mgmt-net | awk '/ id | mac_address / {print $4}')

    # Query and parse required data for creating the OVS port on the
    # integration bridge.
    id_and_mac=($port_id_and_mac)
    MGMT_PORT_ID=${id_and_mac[0]}
    MGMT_PORT_MAC=${id_and_mac[1]}
    MGMT_PORT_IP=$(neutron port-show $MGMT_PORT_ID | awk '/ "ip_address": / {print $7; exit}' | \
         sed -e 's/"//g' -e 's/,//g' -e 's/}//g')

    CONTROLLER_IP_LIST+="$MGMT_PORT_IP:5555, "

    cat << EOF_BR_INT | \
        ssh -o StrictHostKeyChecking=no heat-admin@$node "sudo bash -c \"cat > /etc/sysconfig/network-scripts/ifcfg-br-int\""
DEVICETYPE=ovs
TYPE=OVSBridge
BOOTPROTO=none
DEVICE=br-int
NM_CONTROLLED=no
ONBOOT=yes
EOF_BR_INT

    # Create the OVS port on each controller node for the neutron port.
    MGMT_PORT_DEV=o-hm0

    # Create an interface configuration file for the port so it is properly
    # configured on reboot.
    cat << EOF_PORT_CFG | \
        ssh -o StrictHostKeyChecking=no heat-admin@$node "sudo bash -c \"cat > /etc/sysconfig/network-scripts/ifcfg-$MGMT_PORT_DEV\""
TYPE=OVSIntPort
OVS_BRIDGE=br-int
DEVICETYPE=ovs
BOOTPROTO=static
IPV6_AUTOCONF=no
DEVICE=$MGMT_PORT_DEV
IPADDR=$MGMT_PORT_IP
NETMASK=255.255.255.0
NM_CONTROLLED=no
NETWORK=192.168.199.0
BROADCAST=192.168.199.255
MACADDR=$MGMT_PORT_MAC
OVS_EXTRA="-- set Interface $MGMT_PORT_DEV external-ids:iface-status=active \
    -- set Interface $MGMT_PORT_DEV external-ids:attached-mac=$MGMT_PORT_MAC \
    -- set Interface $MGMT_PORT_DEV external-ids:iface-id=$MGMT_PORT_ID \
    -- set Interface $MGMT_PORT_DEV mac=\"$MGMT_PORT_MAC\" \
    -- set Interface $MGMT_PORT_DEV other-config:hwaddr=$MGMT_PORT_MAC"
ONBOOT=yes
EOF_PORT_CFG
   ssh -o StrictHostKeyChecking=no heat-admin@$node sudo ifup $MGMT_PORT_DEV

   # Bring the interface up.
   ssh -o StrictHostKeyChecking=no heat-admin@$node sudo iptables -I INPUT -i$MGMT_PORT_DEV -p udp --dport 5555 -j ACCEPT

   # Create supplimentary configuration files on each node so the services are
   # configured to use the resources configured in this post deployment step.
   # Note that this uses the config-dir/conf.d configuration facility so we
   # do not have to modify the main configuration file for the service and risk the
   # values being overwritten or removed on a stack update.
   cat << ENDOFWORKER | \
       ssh -o StrictHostKeyChecking=no heat-admin@$node "sudo bash -c \"cat > /etc/octavia/conf.d/octavia-worker/worker-post-deploy.conf\""
[controller_worker]
amp_image_tag = amphora
amp_boot_network_list = $LB_NETWORK_ID
amp_secgroup_list = $LB_SECGROUP_ID
amp_ssh_key_name = octavia-ssh-key

[haproxy_amphora]
user_group = haproxy
key_path = /etc/octavia/.ssh/octavia_ssh_key
# This may need modification if providing certificates other than the sample docs.
client_cert = /etc/octavia/certs/client.pem
server_ca = /etc/octavia/certs/ca_01.pem
ENDOFWORKER
   cat << HLTHMGR | \
       ssh -o StrictHostKeyChecking=no heat-admin@$node "sudo bash -c \"cat > /etc/octavia/conf.d/octavia-health-manager/manager-post-deploy.conf\""
[health_manager]
bind_ip = $MGMT_PORT_IP
HLTHMGR
   cat << NEUTRON_XTRA | \
       ssh -o StrictHostKeyChecking=no heat-admin@$node "sudo bash -c \"cat > /etc/neutron/conf.d/neutron-server/octavia-post-deploy.conf\""
[service_auth]
auth_url =  $OS_AUTH_URL
auth_type = $OS_AUTH_TYPE
admin_user = $OS_USERNAME
admin_password = $OS_PASSWORD
admin_tenant_name = $OS_PROJECT_NAME

[octavia]
request_poll_timeout = 3000
# TODO: This should actually be pointed at a VIP.
base_url = http://$node:9876
NEUTRON_XTRA
   cat << OCTAVIA_XTRA | \
       ssh -o StrictHostKeyChecking=no heat-admin@$node "sudo bash -c \"cat > /etc/octavia/conf.d/common/octavia-post-deploy.conf\""

[service_auth]
auth_url =  $OS_AUTH_URL
auth_type = $OS_AUTH_TYPE
username = $OS_USERNAME
password = $OS_PASSWORD
project_name = $OS_PROJECT_NAME

[DEFAULT]
bind_host = $node

[certificates]
# This may need modification if providing certificates other than the sample docs.
ca_certificate = /etc/octavia/certs/ca_01.pem
ca_private_key = /etc/octavia/certs/private/cakey.pem
ca_private_key_passphrase = foobar
OCTAVIA_XTRA
done

# Now we have to go back and set all of the health managers to have the controller IPs on the
# load balancer network. We also need to restart the services so the new configurations will
# take effect.
CONTROLLER_IP_LIST=${CONTROLLER_IP_LIST::-2}

for rec in $CONTROLLERS;
do
    rec_array=(${rec//=/ })
    node=${rec_array[1]}
    echo "controller_ip_port_list = $CONTROLLER_IP_LIST" | \
       ssh -o StrictHostKeyChecking=no heat-admin@$node "sudo bash -c \"cat >> /etc/octavia/conf.d/octavia-health-manager/manager-post-deploy.conf\""
    ssh -o StrictHostKeyChecking=no heat-admin@$node "sudo systemctl restart octavia-*"
    ssh -o StrictHostKeyChecking=no heat-admin@$node "sudo systemctl restart neutron-*"
done

# NOTE: In future releases, many or all of these post deployment steps will be
# implemented within TripleO itself.
