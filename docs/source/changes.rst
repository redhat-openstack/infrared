New In infrared 2.0
===================

Highlights
----------

#. Workspaces:
    Added `Workspaces <workspace.html>`_. Every session must be tied to an active workspace.
    All input and output file are taken from, and written to, the active workspace directory.
    which allows easy migration of workspace, and avoids accidental overwrites of data,
    or corrupting the working directory.
    The deprecates ``ir-archive`` in favor of ``workspace import`` and ``workspace export``
#. Stand-Alone Plugins:
    Each plugins is fully contained within a single directory.
    `Plugin structure`_ is fully defined and plugins can be loaded from any location on the system.
    `"Example plugin"` shows contributors how to structure their Ansible projects to plug into `infrared`
#. SSH:
    Added ability to establish interactive ssh connection to nodes, managed by workspace
    using workspace's inventory
    ``infrared ssh <hostname>``
#. Single Entry-Point:
    ``ir-provisioner``, ``ir-installer``, ``ir-tester``
    commands are deprecated in favor of a single ``infrared`` entry point (``ir`` also works).
    Type ``infrared --help`` to get the full usage manual.
#. TripleO:
    ``ir-installer ospd`` was broken into two new plugins:
      * `TripleO Undercloud <tripleo-undercloud.html>`_:
        Install undercloud up-to and including overcloud image creation
      * `TripleO Overcloud <tripleo-overcloud.html>`_:
        Install overcloud using an existing undercloud.
#. Answers file:
    The switch ``--generate-conf-file`` is renamed ``--generate-answers-file`` to avoid confusion
    with configuration files.
#. Topology:
    The topology input type has been deprecated. Use `KeyValueList` to define node types and amounts, and ``include_vars``
    to add relevant files to playbooks, see `Topology`_ description for more information
#. Cleanup:
    the ``--cleanup`` options now accepts boolean values. Any YAML boolean is accepted
    ("yes/no", "true/false", "on/off")
#. Bootstrap:
    On virtual environments, `tripleo-undercloud <tripleo-undercloud.html>`_ can create a snapshot
    out of the undercloud VM that can later be used to bypass the installation process.

.. _Plugin structure: plugins.html
.. _Topology: topology.html
.. OVB

Example Script Upgrade
----------------------

.. list-table::
   :header-rows: 1

   * - `infrared` v2
     - `infrared` v1
   * - .. literalinclude:: ../examples/v2_syntax.sh
          :language: bash
     - .. literalinclude:: ../examples/v1_syntax.sh
          :language: bash
