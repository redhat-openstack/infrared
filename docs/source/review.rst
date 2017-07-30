=========================================
Infrared contribute and review guidelines
=========================================

General Notes
=============

Don’t over optimize for a specific CI system (down that road lies madness)
--------------------------------------------------------------------------
Infrared was not built as a CI tool but as an automation tool. This means that
any code contribution should be around general functionality and never tied to
a CI infrastructure.
Remember, CI is but a user of the automation framework. Introducing CI-specific
code paths in the python core or in playbooks will make it impossible to debug
and will reduce the stability for people. CI and automation will diverge from manual
usage, making certain code paths untested in automation, while their counterparts
become unreachable for debugging unless special hacks are used to emulate the
Jenkins environment.
Also, since there’s no guarantees that Jenkins will always be the CI system
used with/by Infrared, any problem that is solved by coupling Infrared to a
specific CI environment/tool will be reintroduced when a new tool is used.

Example for a bad idea: Special code that searches for the ``$WORKSPACE``
environment variable, indicating the executor is a Jenkins build.

.. note:: This example is chosen because it has been suggested on multiple occasions.

Stable API
----------
Changes to API must be backward compatible. Keep in mind that Infrared has 2
active branches - ``master`` and ``stable``.

.. TODO: talk about versions

OpenStack
=========

Infrared is not an openstack project
------------------------------------
Infrared core is designed to provide an “easy-to-use” CLI around Ansible based
projects. Openstack and Tripleo happen to be the main project we use it for, but
don’t expect any form of Openstack knowledge or environment to be present implicitly.
For the same reasons, plugins that aren’t explicit OpenStack plugins, shouldn’t
define OpenStack specific behaviour (ie, don’t hardcode Tripleo specific behaviour
in the “virsh” provisioner plugin).

Legacy Support
--------------
Infrared openstack plugins support OSP 7 (“Kilo” release)  and above. Any
support for previous releases should go in EOL branch. Once OSP 7 reaches its
end of life, it can be dropped as well.

Plugins
=======

Independent
-----------
Plugins should be independent of each other, and shouldn’t rely on other plugins
to be executed previously. The Tempest plugin, for example, expects a working
openstack cloud, but that cloud wasn’t necessarily created with Infrared. It
will look for the cloud credentials in an Infrared-workspace by default, but it
allows the user to provide their own “--openstackrc” file.

Plugins should also be executable as Ansible projects without relying on
Infrared core, and any future  solution to share code, plays, roles, or other
Ansible elements between plugins should take this into account.

Focus
-----
Each plugin should do 1 thing only, and do it well.

Stability and User experience
-----------------------------
The CLI is the face of the plugin. Any new argument hurts the user experience,
and “required” argument even more so. On the other hand, removing or changing
existing arguments will affect users severely. Therefore, we should be very
careful with any change to a plugin.spec file. If information can be discovered
at runtime, we should not make it mandatory for the user to provide it.

Example: openstack ``--version`` is usually discoverable and so it is not
required. It is available because sometimes we want to override that discovery
mechanism (like in case of upgrades).

When adding necessary arguments, try to make them flexible and reusable.
For example, adding an argument to overwrite a value in an ``INI`` file is an
easy change to both the spec file and the play, but it is better to create a
mechanism that will allow the user to edit any and all values in that file with
a single argument (Take a look at ``--config-options`` in ``tempest`` or
``tripleo-undercloud`` plugins for ideas). In that example, even though the
first solution is quicker, in the long run, it will be hard to modify that
argument when more support flexibility will be required.

Ansible Playbooks
=================
Ansible playbooks are not intended to execute line-by-line bash script over SSH.
Ansible is evolving in leaps and bounds and new modules and features are added
and improved in every release. Take the time to learn the tools so you can use
them more effectively.

Modules
-------
Always prefer Ansible built-in modules to raw bash commands (command/shell
modules). They are more readable and more flexible. Ansible modules are
required to be idempotent and handle multiple scenarios and input types. They
can continue without failure if no action is required and provide a standard
API that prevents the need to parse bash outputs. The Ansible community is
quick release new enhancements and fix known bugs.

Ansible modules also provide feedback that increase the ability to control the
playbook flow (``when: task|skipped``) A common example for this is the usage of
``os_*`` modules over mini bash scripts that are required to execute and parse
openstack commands over CLI.

Parsing
-------
Prefer Ansible tools (dict manipulation and Jinja filters) for parsing data,
over complicated bash awk/sed/grep operations. They tend to be more readable,
and are easier to maintain, since not everyone have advanced bash skills, but
anyone writing Ansible playbook should learn Ansible.

Facts and variables
-------------------
When playing with variables it’s important to remember Ansible’s Zen about
variable precedence and try to limit the scope of a variable to where it is needed.

We are often tempted to use ``set_fact`` to define helper variables and pass
them between tasks and plays. Here are the some reasons to resist that urge:

* Ansible variables are immutable, and can only be overwritten or overridden.
* The “set_fact” module defines global variables. We might not know what variables
  we are overwriting or might overwrite that fact later.
* Adds an unnecessary task that will show up in console log (both when executed
  and when skipped)

Usage of “set_fact” can almost always be replaced with proper usage of previous
task’s registered output and play/task vars.

A note about loops, conditionals and vars
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
understanding the way Ansible handles variables can improve playbooks readability
and efficiency. Ansible tasks are YAML representation of a dict and the order their
elements can be written in any order. This example is written in the order Ansible
evaluates the elements to better visualize it.

.. code-block:: yaml

   ---
   - name: a loop with variables and conditions
     with_items: "{{ list_of_dict_itmes|default([]) }}"
     vars:
         a: "{{ tiem.some_value}}"
         b: "{{ list_of_dict_items | selectattr('name', 'equalto', a)|first }}"
     when:
       - item.name.startswith("yair-")
       - b.some_other_value
     debug:
         var: b

* Since ``when`` is evaluated last, it cannot skip the task in case loop or vars
  hold bad or undefined values, and these must be escaped or defaulted using
  Ansible and Jinja filters.
* However, we can use ``when`` to filter out loop iterations.
* **Task** ``vars`` **are evaluated by order written** and so we can use them as
  helper variables for each other as well as for the condition and the actual
  task. Making everything more readable.
* ``vars`` (and later ``when``) are re-evaluated for every iteration of the loop
  so we might want to avoid unnecessary complicated logic somewhere else to
  avoid runtime complexity.

Stability - Infrared CI
=======================

“Master” vs “Stable” branches
-----------------------------
Infrared is a living and breathing project and code is added and modified all
the time. Users should use the “stable” for reliability. New code is submitted
to the “master” branch. Because of the following structure, ``master`` branch
can break at any time, while ``stable`` branch is guaranteed (for a given value
of...) to work.

On Commit
---------
Infrared uses GerritHub to review and test changes before they are merged. In
order to save resources, only explicitly affected plugins are tested. For example,
a change to the “tripleo-undercloud” plugin will not trigger testing of overcloud
creation, or Tempest execution, and changes to a provisioner plugin (``virsh``
or ``openstack``) will only tests that nodes are created and added to the
inventory properly. Each patchset will retrigger the tests. Tests can also be
triggered manually by commenting ``retest``.

Why can’t I see my merged code in the “stable” branch?
------------------------------------------------------
Due to the limited nature and scope of pre-merge CI, changes to the ``master``
branch are not available in the ``stable`` branch right away. Instead every
night, ``nightly`` branch is promoted to match the ``master`` branch, and then
a group of integration tests are executed on it. These `Nightly` builds exercise
the various plugin in multiple permutations and input options to cover most of
the common use cases. Once all these tests pass, ``stable`` branch can be
promoted to match the latest verified code (ie ``nightly`` branch).

Risk testing
------------
If a change seems “risky” and might break the ``nightly`` branch, even though it
passes the regular pre-merge gating system, a responsible reviewer/contributor
should trigger the `risk` gating system, and not wait for the Nightly tests to
run post-merge. Each of the post-merge testing jobs (`Nightly`) has a label that
can be used to trigger it as a pre-merge gate. Simply comment ``test LABEL`` in
gerrit.

**Example:** All of the Tripleo gates use virtual machines (``virsh`` or
``openstack`` provisioner based) to test the code. If a change might behave
differently on a fully bare-metal environment, we might want to test it on such
environment pre-merge. Commenting ``test baremetal`` on that gerrit review, will
trigger several tests on a fully bare-metal environment and report the results
to GerritHub.

Risk tests can also be used to verify a fix to a broken master.

.. warning:: Commenting ``test risk`` will trigger the entire post-merge cycle
  on a single patch. This very wasteful and should be used with great care.

Bug Fixes
---------
In case of urgent bug fixes to the ``stable`` branch, use gerrit UI to
cherry-pick merged code from ``master`` branch to ``stable`` without waiting for
the post-merge tests to verify it. Please remember to manually trigger risk
gates to avoid introducing new bugs and breaking the stable branch even further.
