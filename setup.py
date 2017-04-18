import platform
import setuptools

setuptools.setup(
    setup_requires=['pbr'],
    pbr=True)

if all(platform.linux_distribution(supported_dists="redhat")):
    print("Fixing selinux for redhat systems...")
    from infrared.core.utils.selinux_fix import copy_system_selinux
    copy_system_selinux()
