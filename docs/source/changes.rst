New In InfraRed 2.0
===================

#. Profiles:
    Added `Profiles <profile.html>`_. Every session must be tied to an active profile.
    All input and output file are taken from, and written to, the active profile directory.
    which allows easy migration of workspace, and avoids accidental overwrites of data,
    or corrupting the working directory.
    The deprecates ``ir-archive`` in favor of ``profile import`` and ``profile export``
#. Single Entry-Point:
    ``ir-provisioner``, ``ir-installer``, ``ir-tester``
    commands are deprecated in favor of a single ``infrared`` entry point (``ir`` also works).
    Type ``infrared --help`` to get the full usage manual.
#. Stand-Alone Plugins:
    Each plugins is fully contained within a single directory.
    Plugin structure is fully defined and plugins can be loaded from any location on the system.
    `"Example plugin"` shows contributors how to structure their Ansible projects to plug into `InfraRed`
#. Answers file:
    The switch ``--generate-conf-file`` is renamed ``--generate-answers-file`` to avoid confusion
    with configuration files.
#. Topoloy:
    The topology input type has been deprecated. Use `KeyValueList` to define node types and amounts, and ``include_vars``
    to add relevant files to playbooks
#. Cleanup:
    the ``--cleanup`` options now accepts boolean values. Any YAML boolean is accpeted
    ("yes/no", "true/false", "on/off")

.. OVB
.. Rename OSPD to tripleo

