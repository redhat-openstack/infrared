.. highlight:: plain

Virthost packages/repo requirements
===================================

Virsh
-----

UEFI mode related binaries
^^^^^^^^^^^^^^^^^^^^^^^^^^

According to `usage UEFI with QEMU <https://fedoraproject.org/wiki/Using_UEFI_with_QEMU>`_ there is only one way
to get the UEFI mode boot working with VMs, that often requires by Ironic team due to lack of hardware or impossibility
to automate mode switching on baremetal nodes.

1. Add repo with OVMF binaries::

        yum config-manager --add-repo http://www.kraxel.org/repos/firmware.repo

2. Install OVMF binaries::

        yum install  -y edk2.git-ovmf-x64

3. Update QEMU config adding the following to the end of the /etc/libvirt/qemu.conf file::

                nvram = [
                    "/usr/share/edk2.git/ovmf-x64/OVMF_CODE-pure-efi.fd:/usr/share/edk2.git/ovmf-x64/OVMF_VARS-pure-efi.fd"
                ]
4. Restart libvirt service::

        systemctl restart libvirtd

