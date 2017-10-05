Pytest Runner
-------------

Pytest runner provide option to execute test on Tester node

Usage::

    $ ir pytest-runner

This will run default tests for container sanity

Optional arguments::
    * ``--run``: Whether to run the test or only to prepare for it. Default value is 'True'.
    * ``--repo``: Git repo which contain the test. Default value is 'https://code.engineering.redhat.com/gerrit/rhos-qe-core-installer'
    * ``--file``: Location of the pytest file in the git repo. Default value is 'tripleo/container_sanity.py'
