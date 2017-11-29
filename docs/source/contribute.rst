Contribute
==========

Red Hatters
-----------
RedHat Employees should submit their changes via `review.gerrithub.io`_.
Only members of ``rhosqeauto-core`` on group on GerritHub
can submit patches.
Ask any of the current members about it.

You can use git-review (dnf/yum/pip install).
To initialize the directory of ``infrared`` execute ``git review -s``.
Every patch needs to have *Change-Id* in commit message
(``git review -s`` installs post-commit hook to automatically add one).

For some more info about git review usage, read `GerritHub Intro`_ and `OpenStack Infra Manual`_.

.. _`review.gerrithub.io`: https://review.gerrithub.io/#/q/project:redhat-openstack/infrared
.. _`GerritHub Intro`: https://review.gerrithub.io/Documentation/intro-quick.html#_the_life_and_times_of_a_change
.. _`OpenStack Infra Manual`: http://docs.openstack.org/infra/manual/developers.html

Non Red Hatters
---------------
Non-RedHat Employees should file pull requests to the `InfraRed project`_ on GitHub.

.. _`InfraRed project`: https://github.com/redhat-openstack/infrared
