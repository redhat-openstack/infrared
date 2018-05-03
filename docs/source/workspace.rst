.. highlight:: text

Workspaces
^^^^^^^^^^

With `workspaces`, user can manage multiple environments created by `infrared` and alternate between them.
All runtime files (Inventory, hosts, ssh configuration, ansible.cfg, etc...) will be loaded from a workspace directory and all output files
(Inventory, ssh keys, environment settings, facts caches, etc...) will be generated into that directory.


Create:
    Create new workspace. If name isn't provided, `infrared` will generate one based on timestamp::

        infrared workspace create example

        Workspace 'example' added

    .. note:: The create option will not switch to the newly created workspace. In order to switch to the new workspace, the ``checkout`` command should be used

Inventory:
    Fetch workspace inventory file (a symlink to the real file that might be changed by `infrared` executions)::

        infrared workspace inventory

        /home/USER/.infrared/workspaces/example/hosts
Checkout
    Switches to the specified workspace::

        infrared workspace checkout example3

        Now using workspace: 'example3'

    Creates a new workspace if the ``--create`` or ``-c`` is specified and switches to it::

        infrared workspace checkout --create example3

        Workspace 'example3' added
        Now using workspace: 'example3'

    .. note:: Checked out workspace is tracked via a status file in workspaces_dir, which means checked out workspace is persistent across shell sessions.
              You can pass checked out workspace by environment variable ``IR_WORKSPACE``, which is non persistent
              ::

                    ir workspace list
                    | Name   | Is Active   |
                    |--------+-------------|
                    | bee    | True        |
                    | zoo    |             |

                    IR_WORKSPACE=zoo ir workspace list
                    | Name   | Is Active   |
                    |--------+-------------|
                    | bee    |             |
                    | zoo    | True        |

                    ir workspace list
                    | Name   | Is Active   |
                    |--------+-------------|
                    | bee    | True        |
                    | zoo    |             |

    .. warning:: While ``IR_WORKSPACE`` is set `ir workspace checkout` is disabled
              ::

                    export IR_WORKSPACE=zoo
                    ir workspace checkout zoo
                    ERROR   'workspace checkout' command is disabled while IR_WORKSPACE environment variable is set.

List:
    List all workspaces. Active workspace will be marked.::

        infrared workspace list

        +-------------+--------+
        | Name        | Active |
        +-------------+--------+
        | example     |        |
        | example2    |    *   |
        | rdo_testing |        |
        +-------------+--------+

    .. note:: If the ``--active`` switch is given, only the active workspace will be printed

Delete:
    Deletes a workspace::

        infrared workspace delete example

        Workspace 'example' deleted

    Delete multiple workspaces at once::

        infrared workspace delete example1 example2 example3

        Workspace 'example1' deleted
        Workspace 'example2' deleted
        Workspace 'example3' deleted

Cleanup:
    Removes all the files from workspace. Unlike delete, this will keep the workspace namespace and keep it active if it was active before.::

        infrared workspace cleanup example2

Export:
    Package workspace in a tar ball that can be shipped to, and loaded by, other `infrared` instances::

        infrared workspace export

        The active workspace example1 exported to example1.tar

    To export non-active workspaces, or control the output file::

        infrared workspace export -n example2 -f /tmp/look/at/my/workspace

        Workspace example2 exported to /tmp/look/at/my/workspace.tgz

  .. note:: If the ``-K/--copy-keys`` flag is given, SSH keys from outside the workspace directory, will be copied to the workspace directory and the inventory file will be changed accordingly.

Import:
    Load a previously exported workspace (local or remote)::

        infrared workspace import /tmp/look/at/my/new-workspace.tgz
        infrared workspace import http://free.ir/workspaces/newworkspace.tgz

        Workspace new-workspace was imported

    Control the workspace name::

        infrared workspace import /tmp/look/at/my/new-workspace --name example3

        Workspace example3 was imported

Node list:
    List nodes, managed by a specific workspace::

        infrared workspace node-list
        | Name         | Address     | Groups                                                |
        |--------------+-------------+-------------------------------------------------------|
        | controller-0 | 172.16.0.94 | overcloud_nodes, network, controller, openstack_nodes |
        | controller-1 | 172.16.0.97 | overcloud_nodes, network, controller, openstack_nodes |

        infrared workspace node-list --name some_workspace_name

    ``--group`` - list nodes that are member of specific group.

Group list:
    List groups and nodes in them, managed by a specific workspace:

    .. code-block:: console

        infrared workspace group-list
        | Name            | Nodes                              |
        |-----------------+------------------------------------|
        | overcloud_nodes | controller-0, compute-0, compute-1 |
        | undercloud      | undercloud-0                       |

.. note:: To change the directory where Workspaces are managed, edit the ``workspaces_base_folder`` option.
   Check the  `Infrared Configuration <configuration.html>`_ for details.
