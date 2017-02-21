Troubleshoot
============

Ansible Failures
----------------

Unreachable
^^^^^^^^^^^

When Ansible's task fails because of 'UNREACHABLE' reason, try to validate SSH
credentials and make sure that all host are SSH-ables::

    UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh.", "unreachable": true}
