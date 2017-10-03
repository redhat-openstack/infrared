Advance Features
================

Injection points
^^^^^^^^^^^^^^^^

Different people have different use cases which we cannot anticipate in advance.
To solve (partially) this need, we structured our playbooks in a way that breaks the logic into standalone plays.
Furthermore, each logical play can be overriden by the user at the invocation level.

Lets look at an example to make this point more clear.
Looking at our ``virsh`` main playbook, you will see::

    - include: "{{ provision_cleanup | default('cleanup.yml') }}"
      when: provision.cleanup|default(False)

Notice that the ``include:`` first tried to evaluate the variable ``provision_cleanup`` and afterwards defaults to our own cleanup playbook.

This condition allows users to inject their own custom cleanup process while still reuse all of our other playbooks.

Override playbooks
------------------

In this example we'll use a custom playbook to override our cleanup play and replace it with the process described above.
First, lets create an empty playbook called: ``noop.yml``::

    ---
    - name: Just another empty play
      hosts: localhost
      tasks:
        - name: say hello!
          debug:
              msg: "Hello!"

Next, when invoking `infrared`, we will pass the variable that points to our new empty playbook::

   infrared virsh --host-address $HOST --host-key $HOST_KEY --topology-nodes $TOPOLOGY --cleanup_workspace yes -e provision_cleanup=noop.yml

Now lets run see the results::

    PLAY [Just another empty play] *************************************************

    TASK [setup] *******************************************************************
    ok: [localhost]

    TASK [say hello!] **************************************************************
                           [[ previous task time: 0:00:00.459290 = 0.46s / 0.47s ]]
    ok: [localhost] => {
        "msg": "Hello!"
    }

    msg: Hello!

If you have a place you would like to have an injection point and one is not provided, please `contact us <contacts.html>`_.
