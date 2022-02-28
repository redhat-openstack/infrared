Controller replacement
======================

The OSP Director allows to perofrm controller replacement procedure.
More details can be found here: https://access.redhat.com/documentation/en-us/red_hat_openstack_platform/13/html/director_installation_and_usage/sect-scaling_the_overcloud#sect-Replacing_Controller_Nodes


The ``cloud-config`` plugin automates that procedure. Suppose you already have a deployment with more than one controller.

First step is to extend existing deployment with a new controller node. For virtual deployment the ``virsh`` plugin can be used::

    infrared virsh  --topology-nodes controller:1 \
                    --topology-extend True \
                    --host-address my.hypervisor.address \
                    --host-key ~/.ssh/id_rsa


Next step is to perform controller replacement procedure using ``cloud-config`` plugin::

    infrared cloud-config --tasks=replace_controller \
                          --controller-to-remove=controller-0 \
                          --controller-to-add=controller-3 \


This will replace controller-0 with the newly added controller-3 node. Nodes index start from 0.

Currently controller replacement is supported only for OSP13 and above.


Advanced parameters
-------------------

In case the controller to be replaced cannot be connected by ssh, the ``rc_controller_is_reachable`` should be set to ``no``.
This will skip some tasks that should be performed on the controller to be removed::

    infrared cloud-config --tasks=replace_controller \
                          --controller-to-remove=controller-0 \
                          --controller-to-add=controller-3 \
                          -e rc_controller_is_reachable=no