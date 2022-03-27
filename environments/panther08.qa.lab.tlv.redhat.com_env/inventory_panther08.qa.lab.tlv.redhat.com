localhost ansible_connection=local ansible_python_interpreter=python

hypervisor ansible_host=panther08.qa.lab.tlv.redhat.com ansible_user=root ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/panther08.qa.lab.tlv.redhat.com_env/id_rsa_hypervisor_panther08.qa.lab.tlv.redhat.com

undercloud-0 ansible_host=172.16.0.9 ansible_user=stack ansible_ssh_private_key_file=/home/eshulman/git/infrared/environments/panther08.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_panther08.qa.lab.tlv.redhat.com ansible_ssh_common_args='-o ForwardAgent=yes -o ServerAliveInterval=30 -o ControlMaster=auto -o ControlPersist=30 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -W %h:%p -i /home/eshulman/git/infrared/environments/panther08.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_panther08.qa.lab.tlv.redhat.com root@panther08.qa.lab.tlv.redhat.com"' ansible_python_interpreter='/usr/libexec/platform-python'
localhost ansible_connection=local ansible_python_interpreter=python

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

[local]
localhost
