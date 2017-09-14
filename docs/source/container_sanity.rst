Container Sanity
----------------

The container sanity test runner

Usage::

    $ ir container-sanity

This will run container sanity with default values

Optional arguments::
    * ``--run``: Whether to run the test or only to prepare for it. Default value is 'True'.
    * ``--repo``: Git repo which contain the test. Default value is 'https://code.engineering.redhat.com/gerrit/rhos-qe-core-installer'
    * ``--file``: Location of the pytest file in the git repo. Default value is 'tripleo/container_sanity.py'
