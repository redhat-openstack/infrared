.. highlight:: plain

Workspaces
^^^^^^^^^^

With `workspaces`, user can manage several environments created by `infrared` and alternate between them.
All runtime files (Inventory, hosts, ssh configuration, ansible.cfg, etc...) will be loaded from a workspace directory and all output files
(Inventory, ssh keys, environment settings, facts caches, etc...) will be generated into that directory.


Create:
    Create new workspace. If name isn't provided, `infrared` will generate one based on timestamp::

        infrared workspace create example

        Workspace 'example' added
Checkout
    Creates new workspace if it is not present and switches to it::

        infrared workspace checkout example3

        Workspace 'example3' added
        Now using workspace: 'example3'

    .. note:: Checked out workspace is tracked via a status file in workspaces_dir, which means checked out workspace is persistent across shell sessions.
              You can pass checked out workspace by envitonment variable ``IR_WORKSPACE``, which is non persistent
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

        | Name        | Is Active   |
        |-------------+-------------|
        | example     |             |
        | example2    | True        |
        | rdo_testing |             |

Delete:
    Deletes a workspace::

        infrared workspace delete example

        Workspace 'example' deleted

Cleanup:
    Removes all the files from workspace. Unlike delete, this will keep the workspace namespace and keep it active if it was active before.::

        infrared workspace cleanup example2

Export:
    Package workspace in a tar ball that can be shipped to, and loaded by, other `infrared` instances::

        infrared workspace export

        Workspace example2 exported to example2.tar

    To export non-active workspaces, or control the output file::

        infrared workspace export example1 --dest /tmp/look/at/my/workspace

        Workspace example1 exported to /tmp/look/at/my/workspace

Import:
    Load a previously exported workspace::

        infrared workspace import /tmp/look/at/my/newworkspace

        Workspace newworkspace was imported

    Control the workspace name::

        infrared workspace import /tmp/look/at/my/newworkspace --name example3

        Workspace example3 was imported

Node list:
    List nodes, managed by a specific workspace::

        infrared workspace node-list
        | Name         | Address     |
        |--------------+-------------|
        | controller-0 | 172.16.0.94 |
        | controller-1 | 172.16.0.97 |

        infrared workspace node-list --name some_workspace_name

.. note:: To change the directory where Workspaces are managed, edit the ``workspaces_base_folder`` option.
   Check the  `Infrared Configuration <configuration.html>`_ for details.




