localhost ansible_connection=local ansible_python_interpreter=python
localhost ansible_connection=local ansible_python_interpreter=python
hypervisor ansible_host=panther01.qa.lab.tlv.redhat.com ansible_user=root ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_hypervisor_panther01.qa.lab.tlv.redhat.com

undercloud-0 ansible_host=172.16.0.31 ansible_user=stack ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_panther01.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -W %h:%p -i /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_panther01.qa.lab.tlv.redhat.com root@panther01.qa.lab.tlv.redhat.com"' ansible_python_interpreter='/usr/libexec/platform-python'

controller-2 ansible_host=192.0.10.21 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.21:22"'

controller-1 ansible_host=192.0.10.11 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.11:22"'

controller-0 ansible_host=192.0.10.20 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.20:22"'

computehwoffload-0 ansible_host=192.0.90.24 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.24:22"'

computehwoffload-1 ansible_host=192.0.90.8 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.8:22"'

computeovsdpdksriov-0 ansible_host=192.0.10.9 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.9:22"'

computeovsdpdksriov-1 ansible_host=192.0.10.7 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.7:22"'


[local]
localhost

[hypervisor]
hypervisor

[shade]
hypervisor

[undercloud]
undercloud-0

[tester]
undercloud-0

[overcloud_nodes]
controller-2
controller-1
controller-0
computehwoffload-0
computehwoffload-1
computeovsdpdksriov-0
computeovsdpdksriov-1

[openstack_nodes]
controller-2
controller-1
controller-0
computehwoffload-0
computehwoffload-1
computeovsdpdksriov-0
computeovsdpdksriov-1

[controller]
controller-2
controller-1
controller-0

[computehwoffload]
computehwoffload-0
computehwoffload-1

[computeovsdpdksriov]
computeovsdpdksriov-0
computeovsdpdksriov-1


[local]
localhost
