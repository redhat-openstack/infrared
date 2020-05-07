import setuptools
import warnings


def is_redhat():
    try:
        from platform import linux_distribution
    except ImportError as ex:
        # Since Python 3.8 linux_distribution has been removed
        try:
            import distro
        except ImportError as ex:
            warnings.warn(str(ex))
            return False  # this is fine in most of the cases
        else:
            return 'rhel' in distro.like().split()
    else:
        return 'redhat' in linux_distribution(supported_dists='redhat',
                                              full_distribution_name=False)


setuptools.setup(
    setup_requires=['pbr', 'distro'],
    pbr=True)


if is_redhat():
    from infrared.core.utils.selinux_fix import copy_system_selinux
    copy_system_selinux()
