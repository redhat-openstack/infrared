import os
from os.path import join, dirname, abspath
from pip import req
from setuptools import setup, find_packages

import cli

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = req.parse_requirements('requirements.txt', session=False)

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]


def generate_entry_scripts():
    """
    Generates the entry points for the ir-* scripts.
    """

    # at this point we don't have any packages installed
    # so hard-code settings folder for now here
    specs = next(os.walk('settings'))[1]

    return ["ir-{0} = cli.main:entry_point".format(spec_name)
            for spec_name in
            specs]

prj_dir = dirname(abspath(__file__))
setup(
    name='infrared',
    version=cli.__VERSION__,
    packages=find_packages(),
    long_description=open(join(prj_dir, 'README.rst')).read(),
    entry_points={
        'console_scripts': generate_entry_scripts()
    },
    install_requires=reqs,
    author='rhos-qe',
    author_email='rhos-qe-dept@redhat.com'
)

try:
    import selinux
except ImportError as e:
    new_error = type(e)(e.message + ". check that 'python-libselinux is "
                                    "installed'")
    import sys
    import shutil
    from distutils import sysconfig

    if hasattr(sys, 'real_prefix'):
        # check for venv
        VENV_SITE = sysconfig.get_python_lib()
        SELINUX_PATH = os.path.join(
            sysconfig.get_python_lib(plat_specific=True,
                                     prefix=sys.real_prefix),
            "selinux")
        if not os.path.exists(SELINUX_PATH):
            raise new_error
        print("missing selinux binding. Trying to pull modules from "
                 "system ({source}) to virtualenv {dest}".format(
            source=SELINUX_PATH, dest=sys.prefix))

        # filter precompiled files
        files = [f for f in os.listdir(SELINUX_PATH)
                 if not os.path.splitext(f)[1] in (".pyc", ".pyo")]
        dest = os.path.join(VENV_SITE, "selinux")
        os.makedirs(dest)
        for f in files:
            print("Copying {source} to {dest}".format(
                source=f, dest=dest))
            shutil.copy(os.path.join(SELINUX_PATH, f),
                         dest)
    else:
        raise new_error
    import selinux
