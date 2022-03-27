Host hypervisor
    HostName panther01.qa.lab.tlv.redhat.com
    User root
    IdentityFile /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_hypervisor_panther01.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
Host undercloud-0
    HostName 172.16.0.31
    User stack
    IdentityFile /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_panther01.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -W %h:%p -i /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_panther01.qa.lab.tlv.redhat.com root@panther01.qa.lab.tlv.redhat.com
Host controller-2
    HostName 192.0.10.21
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.21:22
Host controller-1
    HostName 192.0.10.11
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.11:22
Host controller-0
    HostName 192.0.10.20
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.20:22
Host computehwoffload-0
    HostName 192.0.90.24
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.24:22
Host computehwoffload-1
    HostName 192.0.90.8
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.8:22
Host computeovsdpdksriov-0
    HostName 192.0.10.9
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.9:22
Host computeovsdpdksriov-1
    HostName 192.0.10.7
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.10.7:22

Host 192.0.*
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther01.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther01.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther01.qa.lab.tlv.redhat.com undercloud-0 -W %h:22
