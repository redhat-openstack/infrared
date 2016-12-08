New In InfraRed 2.0
===================

#. Profiles:
    Added `Profiles <profile.html>`_. Every session must be tied to an active profile.
    All input and output file are taken from, and written to, the active profile directory.
    which allows easy migration of workspace, and avoids accidental overwrites of data,
    or corrupting the working directory.
    The deprecates ``ir-archive`` in favor of ``profile import`` and ``profile export``
#. Single entry points:
    ``ir-*`` (``ir-provisioner``, ``ir-installer``, ``ir-tester``)
    commands are deprecated in favor of a single ``infrared`` entry point.
    Type ``infrared --help`` to get the full usage manual.
#. Stand-Alone Plugins:
    Each plugins is fully contained within a single directory.
    Plugin structure is fully defined and plugins can be loaded from any location on the system.
    `"Example plugin"` shows contributors how to structure their Ansible projects to plug into `InfraRed`
#. OVB:
    Support installing TripleO on "OpenStack" provisioned virtual machines, from properly configured clouds.
