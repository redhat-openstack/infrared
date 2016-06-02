.. highlight:: plain

Advanced features
=================

Scalability
^^^^^^^^^^^

Infrared allows to perform scale tests on different services.

Currently supported services for tests:
    * compute
    * ceph-storage
    * swift-storage

#. To scale compute service:

    Deployment should have at least 3 compute nodes.

    Run ansible playbook::

        ansible-playbook -vvvv -i hosts -e @install.yml playbooks/installer/ospd/post_install/scale_compute.yml

    It will scale compute nodes down to 1 and after that scale compute node back to 3.

#. To scale ceph-storage service:

    Deployment should have at least 3 ceph-storage nodes.

    Run ansible playbook::

        ansible-playbook -vvvv -i hosts -e @install.yml playbooks/installer/ospd/post_install/ceph_compute.yml

    It will scale compute nodes down to 1 and after that scale compute node back to 3.

#. To scale swift-storage service:

    Deployment should have at least 3 swift-storage nodes.

    Run ansible playbook::

            ansible-playbook -vvvv -i hosts -e @install.yml playbooks/installer/ospd/post_install/swift_compute.yml

    .. note:: Swift has a parameter called ``min_part_hours`` which configures amount of time that should be passed between two rebalance processes. In real production environment this parameter is used to reduce network load. During the deployment of swift cluster for further scale testing we set it to 0 to decrease amount of time for scale.

