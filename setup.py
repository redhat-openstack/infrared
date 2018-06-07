from __future__ import print_function
import platform
import setuptools
import sys

setuptools.setup(
    setup_requires=['pbr'],
    pbr=True)

if 'redhat' in platform.linux_distribution(
        supported_dists='redhat',
        full_distribution_name=False):
    print("Fixing selinux for redhat systems...", file=sys.stderr)
    from infrared.core.utils.selinux_fix import copy_system_selinux
    copy_system_selinux()
