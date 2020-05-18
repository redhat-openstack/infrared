import os
import subprocess
import sys
import warnings

import setuptools


setuptools.setup(
    setup_requires=['pbr', 'distro'],
    pbr=True)


def has_selinux():
    """Checks has system SE Linux bindings

    Import SE Linux bindings from base executable before copying files to
    ensure can actually use SE Linux
    """

    prefix = (getattr(sys, 'real_prefix', None) or
              getattr(sys, 'base_prefix', None) or
              sys.prefix)
    command = 'python{major}.{minor}'.format(major=sys.version_info.major,
                                             minor=sys.version_info.minor)
    executable = os.path.join(prefix, 'bin', command)
    try:
        subprocess.check_call([executable, '-c', 'import selinux'],
                              universal_newlines=True)
    except subprocess.CalledProcessError as ex:
        warnings.warn(str(ex))
        return False
    return True


if has_selinux():
    from infrared.core.utils.selinux_fix import copy_system_selinux
    copy_system_selinux()
