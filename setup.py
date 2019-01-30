import platform
import setuptools
import sys

setuptools.setup(
    setup_requires=['pbr'],
    pbr=True)

if 'redhat' in platform.linux_distribution(
        supported_dists='redhat',
        full_distribution_name=False):
    if sys.version_info[0] < 3:
        from infrared.core.utils.selinux_fix import copy_system_selinux
        copy_system_selinux()
