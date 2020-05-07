import setuptools


setuptools.setup(setup_requires=['pbr'], pbr=True)


def is_redhat():
    try:
        from platform import linux_distribution
    except ImportError:
        # Since Python 3.5 linux_distribution has been deprecated and
        # since Python 3.8 linux_distribution has been removed
        import distro
        return 'rhel' in distro.like().split()

    return 'redhat' in linux_distribution(supported_dists='redhat',
                                          full_distribution_name=False)


if is_redhat():
    from infrared.core.utils.selinux_fix import copy_system_selinux
    copy_system_selinux()
