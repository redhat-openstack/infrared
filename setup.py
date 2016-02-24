from os.path import join, dirname, abspath
from pip import req
from setuptools import setup, find_packages

import cli

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = req.parse_requirements('requirements.txt', session=False)

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

# InfraRed scripts
cmds = ('provision', 'install', 'test')
scripts = ['ir-' + cmd for cmd in cmds]

prj_dir = dirname(abspath(__file__))
setup(
    name='infrared',
    version=cli.__VERSION__,
    packages=find_packages(),
    long_description=open(join(prj_dir, 'README.rst')).read(),
    entry_points={
        'console_scripts': [script + ' = cli.main:main' for script in scripts]
    },
    install_requires=reqs,
    author='Yair Fried',
    author_email='yfried@redhat.com'
)
