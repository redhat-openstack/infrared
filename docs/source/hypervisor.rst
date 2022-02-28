.. _hypervisor:

Hypervisor machine
------------------

Hypervisor machine is the target machine where `infrared`'s virsh provisioner will create
virtual machines and networks (using libvirt) to emulate baremetal infrastructure.

As such there are several specific requirements it has to meet.

Generally, It needs to have **enough memory and disk** storage to hold multiple decent VMs
(each with GBytes of RAM and dozens of GB of disk).
Also for acceptable responsiveness (speed of deployment/testing) just <4 threads or low GHz
CPU is not a recommended choice  (if you have old and weaker CPU than current mid-high end mobile
phone CPU you may suffer performance wise - and so more timeouts during deployment or in tests).


Especially, for Ironic (TripleO) to control them, those **libvirt VMs** need to be bootable/controllable
for **iPXE provisioning**.
And also extra user has to exist, which can ssh in the hypervisor and control (restart...) libvirt VMs.

.. note:: `infrared` is attempting to configure or validate all (most) of this but it's may be
          scattered across all provisioner/installer steps. Current infrared approach is stepped
          toward direction to be more idempotent, and failures on previous runs shouldn't prevent
          successful execution of following runs.

What **user has to provide**:

    - have machine with **sudoer user ssh access** and **enough resources**,
      as minimum requirements for one VM are:

      + VCPU: 2|4|8
      + RAM: 8|16
      + HDD: 40GB+
      + in practice disk may be smaller, as they are thin provisioned,
        as long as you don't force writing all the data (aka Tempest with rhel-guest instead of cirros etc)

    - **RHEL-7.3** and **RHEL-7.4** are tested, **CentOS** is also expected to work

      + may work with other distributions (best-effort/limited support)

    - **yum repositories** has to be **preconfigured** by user (foreman/...) before using `infrared` so it can install dependencies

      + esp. for `infrared` to handle ``ipxe-roms-qemu`` it requires either **RHEL-7.{3|4}-server channel**

What **infrared takes care of**:

    - ``ipxe-roms-qemu`` package of at least ``version 2016xxyy`` needs to be installed

    - other basic packages installed

      + ``libvirt``, ``libguestfs{-tools,-xfs}``, ``qemu-kvm``, ``wget``, ``virt-install``

    - **virtualization support** (VT-x/AMD-V)

      + ideally with **nested=1** support

    - ``stack`` user created with polkit privileges for *org.libvirt.unix.manage*
    - **ssh key** with which `infrared` can authenticate (created and) added for *root* and *stack* user,
      ATM they are handled differently/separately:

      + for *root* the ``infared/id_rsa.pub`` gets added to authorized_keys
      + for *stack* ``infrared/id_rsa_undercloud.pub`` is added to authorized_keys, created/added later during installation
