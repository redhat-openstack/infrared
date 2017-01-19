Profiles
^^^^^^^^

With `profiles`, user can manage several environments created by `InfraRed` and alternate between them.
All runtime files (Inventory, hosts, ssh configuration, ansible.cfg, etc...) will be loaded from a profile directory and all output files
(Inventory, ssh keys, environment settings, facts caches, etc...) will be generated into that directory.


Create:
    Create new profile. If name isn't provided, InfraRed will generate one based on timestamp::

        infrared profile create example

        Profile 'example' added
Checkout
    Creates new profile if it is not present and switches to it::

        infrared profile checkout example3

        Profile 'example3' added
        Now using profile: 'example3'
Delete:
    Deletes a profile::

        infrared profile delete example

        Profile 'example' deleted
Activate
    Set the active profile::

        infrared profile active example2

        Profile has been activated

.. note:: Checked out profile is tracked via a status file in profiles_dir, which means checked out profile is persistent across shell sessions.
          You can pass checked out profile by envitonment vriable ``IR_CHECKEDOUT_PROFILE``, which is non persistent::

    ir profile list
    | Name   | Is Active   |
    |--------+-------------|
    | bee    | True        |
    | zoo    |             |

    IR_CHECKEDOUT_PROFILE=zoo ir profile list
    | Name   | Is Active   |
    |--------+-------------|
    | bee    |             |
    | zoo    | True        |

    ir profile list
    | Name   | Is Active   |
    |--------+-------------|
    | bee    | True        |
    | zoo    |             |

.. warning:: While ``IR_CHECKEDOUT_PROFILE`` is set `ir profile checkout` is disabled::

    export IR_CHECKEDOUT_PROFILE=zoo
    ir profile checkout zoo
    ERROR   'profile checkout' command is disabled while IR_CHECKEDOUT_PROFILE environment variable is set.

List:
    List all profiles. Active profile will be marked.::

        infrared profile list

        | Name        | Is Active   |
        |-------------+-------------|
        | example     |             |
        | example2    | True        |
        | rdo_testing |             |
Cleanup:
    Removes all the files from profile. Unlike delete, this will keep the profile namespace and keep it active if it was active before.::

        infrared profile cleanup example2

Export:
    Package profile in a tar ball that can be shipped to, and loaded by, other `infrared` instances::

        infrared profile export

        Profile example2 exported to example2.tar

    To export non-active profiles, or control the output file::

        infrared profile export example1 --dest /tmp/look/at/my/profile

        Profile example1 exported to /tmp/look/at/my/profile

Import:
    Load a previously exported profile::

        infrared profile import /tmp/look/at/my/newprofile

        Profile newprofile was imported

    Control the profile name::

        infrared profile import /tmp/look/at/my/newprofile --name example3

        Profile example3 was imported

Node list:
    List nodes, managed by a specific profile::

        infrared profile node-list
        | Name         | Address     |
        |--------------+-------------|
        | controller-0 | 172.16.0.94 |
        | controller-1 | 172.16.0.97 |

        infrared profile node-list --name some_profile_name

.. note:: To change the directory where Profiles are managed, edit the ``profiles_base_folder`` option.
   Check the  `Infrared Configuration <configuration.html>`_ for details.




