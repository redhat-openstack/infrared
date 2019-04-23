.. highlight:: text

Setup
=====

Ansible Configuration
---------------------
Config file(`ansible.cfg <http://docs.ansible.com/ansible/latest/intro_configuration.html>`_) could be provided to get custom behavior for Ansible.

Infrared try to locate the Ansible config file(ansible.cfg) in several locations, in the following order:

   * ANSIBLE_CONFIG (an environment variable)
   * ansible.cfg (in the current directory)
   * ansible.cfg (in the Infrared home directory)
   * .ansible.cfg (in the home directory)

If none of this location contains Ansible config, InfraRed will create a default one in Infrared's home directory

.. literalinclude:: ../examples/ansible.cfg
   :linenos:

.. note:: Values for `forks`, `host_key_checking` and `timeout` have to be the same or greater.

Bash completion
---------------
Bash completion script is in etc/bash_completion.d directory of git repository.
To enable global completion copy this script to proper path in the system (/etc/bash_completion.d)::

  cp etc/bash_completion.d/infrared /etc/bash_completion.d/

Alternatively, just source it to enable completion temporarily::

  source etc/bash_completion.d/infrared

When working in virtualenv, might be a good idea to add import of this script to the
virtualenv activation one::

  echo ". $(pwd)/etc/bash_completion/infrared" >> ${VIRTUAL_ENV}/bin/activate
