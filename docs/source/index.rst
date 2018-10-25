.. infrared documentation master file, created by
   sphinx-quickstart on Wed Dec  7 11:34:21 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================
What is InfraRed?
=================

InfraRed is a plugin based system that aims to provide an easy-to-use CLI for Ansible based projects.
It aims to leverage the power of Ansible in managing / deploying systems, while providing an alternative, fully customized,
CLI experience that can be used by anyone, without prior Ansible knowledge.

The project originated from Red Hat OpenStack infrastructure team that looked for a solution to provide an "easier" method
for installing OpenStack from CLI but has since grown and can be used for *any* Ansible based projects.

Welcome to infrared's documentation!
====================================

.. toctree::
   :maxdepth: 2
   :caption: Core

   bootstrap
   setup
   configuration
   workspace
   plugins
   topology
   interactive_ssh
   changes
   advance_features
   contacts
   contribute
   ovb
   troubleshoot.rst
   current_temporary_hacks.rst

.. toctree::
   :maxdepth: 2
   :caption: Plugins

   baremetal
   beaker
   foreman
   openstack_provisioner
   virsh
   tripleo-undercloud
   tripleo_upgrade
   tripleo-overcloud
   cloud-config
   tempest
   collect-logs
   gabbi_tester
   list_builds
   pytest_runner
   ospdui_tester

.. toctree::
   :maxdepth: 2
   :caption: Cookbook

   rdo
   splitstack
   composable_roles
   cdn_cookbook.rst
   hybrid_deployment
   plugins_guide
   control_placement
   controller_replacement
   standalone_deployment

.. toctree::
   :maxdepth: 2
   :caption: Release notes

   release_notes

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
