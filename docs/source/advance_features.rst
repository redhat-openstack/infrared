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

   infrared virsh --host-address $HOST --host-key $HOST_KEY --topology-nodes $TOPOLOGY --kill yes -e provision_cleanup=noop.yml

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


Infrared Ansible Tags
^^^^^^^^^^^^^^^^^^^^^

Stages and their corresponding Ansible tags
-------------------------------------------

Each stage can be executed using ansible plugin with set of ansible tags that are passed to the infrared plugin command:


+--------------------+-------------------+-----------------------------------------------------------------+
| Plugin             | Stage             | Ansible Tags                                                    |
+====================+===================+=================================================================+
| virsh              | Provision         | pre, hypervisor, networks, vms, user, post                      |
+--------------------+-------------------+-----------------------------------------------------------------+
| tripleo-undercloud | Undercloud Deploy | validation, hypervisor, init, install, shade, configure, deploy |
+                    +-------------------+-----------------------------------------------------------------+
|                    | Images            | images                                                          |
+--------------------+-------------------+-----------------------------------------------------------------+
| tripleo-overcloud  | Introspection     | validation, init, introspect                                    |
+                    +-------------------+-----------------------------------------------------------------+
|                    | Tagging           | tag                                                             |
+                    +-------------------+-----------------------------------------------------------------+
|                    | Overcloud Deploy  | loadbalancer, deploy_preparation, deploy                        |
+                    +-------------------+-----------------------------------------------------------------+
|                    | Post tasks        | post                                                            |
+--------------------+-------------------+-----------------------------------------------------------------+


Usage examples:
***************

The ansible tags can be used by passing all subsequent input to Ansible as raw arguments.

Provision (virsh plugin)::

    infrared virsh \
        -o provision_settings.yml \
        --topology-nodes undercloud:1,controller:1,compute:1 \
        --host-address <my.host.redhat.com> \
        --host-key </path/to/host/key \
        --image-url <image-url>
        --ansible-args="tags=pre,hypervisor,networks,vms,user,post"

Undercloud Deploy stage (tripleo-undercloud plugin)::

    infrared tripleo-undercloud \
        -o undercloud_settings.yml \
        --mirror tlv \
        --version 12 \
        --build passed_phase1 \
        --ansible-args="tags=validation,hypervisor,init,install,shade,configure,deploy"

Tags explanation:
-----------------

- Provision
    - pre - Pre run configuration
    - Hypervisor - Prepare the hypervisor for provisioning
    - Networks - Create Networks
    - Vms - Provision Vms
    - User - Create a sudoer user for non root SSH login
    - Post - perform post provision tasks
- Undercloud Deploy
    - Validation - Perform validations
    - Hypervisor - Patch hypervisor for undercloud deployment
        - Add rhos-release repos and update ipxe-roms
        - Create the stack user on the hypervisor and allow SSH to hypervisor
    - Init - Pre Run Adjustments
    - Install - Configure and Install Undercloud Repositories
    - Shade - Prepare shade node
    - Configure - Configure Undercloud
    - Deploy - Installing the undercloud
- Images
    - Images - Get the undercloud version and prepare the images
- Introspection
    - Validation - Perform validations
    - Init - pre-tasks
    - Introspect - Introspect our machines
- Tagging
    - Tag - Tag our machines with proper flavors
- Overcloud Deploy
    - Loadbalancer - Provision loadbalancer node
    - Deploy_preparation - Environment setup
    - Deploy - Deploy the Overcloud
- Post tasks
    - Post - Perform post install tasks

