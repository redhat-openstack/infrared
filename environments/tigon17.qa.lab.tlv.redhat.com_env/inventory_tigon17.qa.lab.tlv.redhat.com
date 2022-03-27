localhost ansible_connection=local ansible_python_interpreter=python

controller-2 ansible_host=192.0.90.12 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.12:22"'

controller-1 ansible_host=192.0.90.23 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.23:22"'

controller-0 ansible_host=192.0.90.11 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.11:22"'

computehwoffload-0 ansible_host=192.0.90.24 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.24:22"'

computehwoffload-1 ansible_host=192.0.90.8 ansible_user=heat-admin ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.8:22"'
localhost ansible_connection=local ansible_python_interpreter=python
hypervisor ansible_host=tigon17.qa.lab.tlv.redhat.com ansible_user=root ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_hypervisor_tigon17.qa.lab.tlv.redhat.com

undercloud-0 ansible_host=172.16.0.36 ansible_user=stack ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_tigon17.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -W %h:%p -i /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_tigon17.qa.lab.tlv.redhat.com root@tigon17.qa.lab.tlv.redhat.com"' ansible_python_interpreter='/usr/libexec/platform-python'


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

[openstack_nodes]
controller-2
controller-1
controller-0
computehwoffload-0
computehwoffload-1

[controller]
controller-2
controller-1
controller-0

[computehwoffload]
computehwoffload-0
computehwoffload-1


[local]
localhost
