.. include:: warning.txt

Contributors Guide
==================

Sending patches
---------------
Changes to project are accepted via `review.gerrithub.io`_.
For that you need to be member of our group rhosqeauto-core on gerrithub,
ask any of the current members about it.

You can use git-review (dnf/yum/pip install).
To initalize in the directory of InfraRed execute ``git review -s``.
Every patch needs to have *Change-Id* in commit message
(git review -s installs post-commit hook to automatically add one).

For some more info about git review usage, read `GerritHub Intro`_ and `OpenStack Infra Manual`_.

.. _`review.gerrithub.io`: https://review.gerrithub.io/#/q/project:rhosqeauto/InfraRed
.. _`GerritHub Intro`: https://review.gerrithub.io/Documentation/intro-quick.html#_the_life_and_times_of_a_change
.. _`OpenStack Infra Manual`: http://docs.openstack.org/infra/manual/developers.html
