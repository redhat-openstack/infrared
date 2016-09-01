from setuptools import setup, find_packages


setup(
    name='infra-core',
    version='0.0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            "infrared = infrared.main:main"
        ]
    },
    author='',
    author_email=''
)
