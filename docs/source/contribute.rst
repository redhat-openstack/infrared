Contribute
==========

Red Hatters
-----------
RedHat Employees should submit their changes via `review.gerrithub.io`_.

To upload new reviews or vote on existing ones,
membership in at least `rhosqeauto-contrib`_ is needed.

Ask any existing `members of rhosqeauto-core`_ or `members of rhos-ci`_ groups to add You in there.

Only members of ``rhosqeauto-core`` (includes ``rhos-ci``) can submit (merge) the patches on review.

You can use git-review (dnf/yum/pip install).
To initialize the directory of ``infrared`` execute ``git review -s``.
Every patch needs to have *Change-Id* in commit message
(``git review -s`` installs post-commit hook to automatically add one).

For some more info about git review usage, read `GerritHub Intro`_ and `OpenStack Infra Manual`_.

.. _`review.gerrithub.io`: https://review.gerrithub.io/#/q/project:redhat-openstack/infrared
.. _`members of rhosqeauto-core`: https://review.gerrithub.io/admin/groups/48250c57af5cae14ac05aba80badf7d1398635a6,members
.. _`members of rhos-ci`: https://review.gerrithub.io/admin/groups/88a9891fd3e54031d81363738e0d4db93b027dd9,members
.. _`rhosqeauto-contrib`: https://review.gerrithub.io/admin/groups/6bb5f78d4182efb8d965219c5b183ba5d989d89a,members
.. _`GerritHub Intro`: https://review.gerrithub.io/Documentation/intro-quick.html#_the_life_and_times_of_a_change
.. _`OpenStack Infra Manual`: http://docs.openstack.org/infra/manual/developers.html

Non Red Hatters
---------------
Non-RedHat Employees should file pull requests to the `InfraRed project`_ on GitHub.

.. _`InfraRed project`: https://github.com/redhat-openstack/infrared


Release Notes
-------------
Infrared uses `reno`_ tool for providing release notes.
That means that a patch can include a reno file (release notes) containing detailed description what the impact is.

A reno file is a YAML file written in the releasenotes/notes directory which is generated using the reno tool this way:

    .. code-block:: shell

      $ tox -e venv -- reno new <name-your-file>


where <name-your-file> can be:
    - bugfix-<bug_name_or_id>
    - newfeature-<feature_name>
    - apichange-<description>
    - deprecation-<description>

Refer to the reno documentation for the full list of sections.

.. _`reno`: https://docs.openstack.org/reno/latest/



When a release note is needed
-----------------------------
A release note is required anytime a reno section is needed. Below are some examples for each section.
Any sections that would be blank should be left out of the note file entirely.

upgrade
  A configuration option change (deprecation, removal or modified default), changes in core that can affect users of the
  previous release. Any changes in the Infrared API.

security
  If the patch fixes a known vulnerability

features
  New feature in Infrared core or a new major feature in one of a core plugin. Introducing of the new API options or CLI
  flags.

critical
  Bugfixes categorized as Critical and above in Jira.

fixes
  Bugs with high importance that have been fixed.


Three sections are left intentionally unexplained (``prelude``, ``issues`` and ``other``).
Those are targeted to be filled in close to the release time for providing details about the soon-ish release.
Don't use them unless you know exactly what you are doing.
