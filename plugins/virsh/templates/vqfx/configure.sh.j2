#!/bin/bash
set -x

# copy ssh key to the instance
expect -c "
spawn bash -c \"ssh-copy-id -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i {{ switch_ssh_key }} {{ switch_ip }}\"
expect \"Password:\"
send \"Juniper\r\"
expect \"Number of key(s) added: 1\"
"

expect -c"
  set timeout 300
  spawn ssh root@{{ switch_ip }} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
  expect \"root@:RE:0%\"
  send \"cli\r\"
  expect \"root>\"
  send \"config\r\"
  expect \"root#\"
  send \"set interfaces em1 unit 0 family inet address 169.254.0.2/24\r\"
  expect \"root#\"
  send \"commit\r\"
  expect \"root#\"
  send \"exit\r\"
  expect \"root>\"
  send \"restart chassis-control\r\"
  expect \"root>\"
  send \"exit\r\"
  expect \"root@:RE:0%\"
  send \"exit\r\"
"

sleep 60

# copy the infterface wait script into the appliance
scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {{ temp_dir.path }}/vqfx_wait.sh root@{{ switch_ip }}:~/wait.sh

# wait for interfaces to come up, then configure
expect -c"
  set timeout 300
  spawn ssh root@{{ switch_ip }} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
  expect \"root@:RE:0%\"
  send \"csh wait.sh\r\"
  expect \"root@:RE:0%*\"
  send \"cli\r\"
  expect \"root>\"
  send \"config\r\"
  expect \"root#\"
  send \"set vlans br-tenant vlan-id 37\r\"
  expect \"root#\"
  send \"set interfaces interface-range br-tenant unit 0 family ethernet-switching vlan members br-tenant\r\"
  expect \"root#\"
  send \"set interfaces irb unit 1 family inet address 192.168.2.250/24\r\"
  expect \"root#\"
  send \"set vlans default l3-interface irb.1\r\"
  expect \"root#\"
  send \"set interfaces xe-0/0/0 unit 0 family ethernet-switching vlan members default\r\"
  expect \"root#\"
  send \"set interfaces xe-0/0/1 unit 0 family ethernet-switching vlan members default\r\"
  expect \"root#\"
  send \"set interfaces interface-range br-tenant member-range xe-0/0/0 to xe-0/0/1\r\"
  expect \"root#\"
  send \"set interfaces interface-range br-tenant native-vlan-id 37\r\"
  expect \"root#\"
  send \"delete interfaces interface-range br-tenant unit 0 family ethernet-switching vlan members br-tenant\r\"
  expect \"root#\"
  send \"set interfaces interface-range br-tenant unit 0 family ethernet-switching interface-mode trunk\r\"
  expect \"root#\"
  send \"set interfaces interface-range br-tenant unit 0 family ethernet-switching vlan members br-tenant\r\"
  expect \"root#\"
  send \"commit\r\"
  expect \"root#\"
  send \"exit\r\"
  expect \"root>\"
  send \"exit\r\"
  expect \"root@:RE:0%\"
  send \"exit\r\"
"
