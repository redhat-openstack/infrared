.. include:: warning.txt

Introduction
============
InfraRed is tool used for automated deployments of various OpenStack environments. It does not try to be focused on CI use-cases only, it is focused on automation in general. It is written in Python 2.7 and using `Ansible <https://www.ansible.com>`_ as deployment backend. Python dependencies are handled by `pip <https://pip.pypa.io/en/stable/>`_ package manager.

Workflow is divided into 3 separated steps:

#. Provisioning (ir-provisioner tool)

#. Installation (ir-installer tool)

#. Testing (ir-tester tool)

Please see `Setup <quickstart.html>`_ page first or proceed to guide for impatient (`Quickstart <quickstart.html>`_).
