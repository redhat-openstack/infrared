from setuptools import setup, find_packages
from os.path import join, dirname, abspath
import ksgen


prj_dir = dirname(abspath(__file__))
setup(
    name='ksgen',
    version=ksgen.__VERSION__,
    packages=find_packages(),
    long_description=open(join(prj_dir, 'README.rst')).read(),
    entry_points={
        'console_scripts': ['ksgen = ksgen.core:main']
    },
    install_requires=[
        'docopt',
        'PyYAML',
        'configure'
    ],
    author='Sunil Thaha',
    author_email='sthaha@redhat.com'
)
