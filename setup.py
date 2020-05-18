import subprocess
import sys
import setuptools


setuptools.setup(
    setup_requires=['pbr', 'distro'],
    pbr=True)

subprocess.check_call([sys.executable, 'infrared/core/utils/selinux_fix.py'])
