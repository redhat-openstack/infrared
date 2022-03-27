Host controller-2
    HostName 192.0.90.12
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.12:22
Host controller-1
    HostName 192.0.90.23
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.23:22
Host controller-0
    HostName 192.0.90.11
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.11:22
Host computehwoffload-0
    HostName 192.0.90.24
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.24:22
Host computehwoffload-1
    HostName 192.0.90.8
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W 192.0.90.8:22
Host hypervisor
    HostName tigon17.qa.lab.tlv.redhat.com
    User root
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_hypervisor_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
Host undercloud-0
    HostName 172.16.0.36
    User stack
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -W %h:%p -i /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_tigon17.qa.lab.tlv.redhat.com root@tigon17.qa.lab.tlv.redhat.com

Host 192.0.*
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_tigon17.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/tigon17.qa.lab.tlv.redhat.com_env/ansible.ssh.config.tigon17.qa.lab.tlv.redhat.com undercloud-0 -W %h:22
