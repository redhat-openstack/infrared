Host hypervisor
    HostName panther08.qa.lab.tlv.redhat.com
    User root
    IdentityFile /home/eshulman/git/infrared/environments/panther08.qa.lab.tlv.redhat.com_env/id_rsa_hypervisor_panther08.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
Host undercloud-0
    HostName 172.16.0.9
    User stack
    IdentityFile /home/eshulman/git/infrared/environments/panther08.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_panther08.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -W %h:%p -i /home/eshulman/git/infrared/environments/panther08.qa.lab.tlv.redhat.com_env/id_rsa_undercloud_panther08.qa.lab.tlv.redhat.com root@panther08.qa.lab.tlv.redhat.com

Host 192.168.*
    User heat-admin
    IdentityFile /home/eshulman/git/infrared/environments/panther08.qa.lab.tlv.redhat.com_env/id_rsa_overcloud_panther08.qa.lab.tlv.redhat.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ForwardAgent yes
    ProxyCommand ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -F /home/eshulman/git/infrared/environments/panther08.qa.lab.tlv.redhat.com_env/ansible.ssh.config.panther08.qa.lab.tlv.redhat.com undercloud-0 -W %h:22
