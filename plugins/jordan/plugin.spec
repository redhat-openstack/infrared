---
plugin_type: test
subparsers:
    jorden:
        description:
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
          - title: Cluster Tests
            options:
                check-cluster:
                    type: Bool
                    help: Specify whether to run Ceph cluster validation
                    default: True

          - title: Ceph monitor nodes
            options:
                check-monitors:
                    type: Bool
                    help: Specify whether to run monitor services validation
                    default: True

                monitor-nodes:
                    type: Value
                    help: The node type on which Ceph's monitors are running
                    default: controller

          - title: Ceph OSD nodes
            options:
                check-osds:
                    type: Bool
                    help: Specify whether to run OSDs services validation
                    default: True

                osds-number:
                    type: Value
                    help: the number of OSDs in the cluster
                    default: 3

          - title: Ceph pools
            options:
                check-pools:
                    type: Bool
                    help: Specify whether to run pools parameters validation
                    default: True

                ceph-pools:
                    type: Value
                    help: the names of the deployed pools
                    default: volumes,images,vms,metrics,backups

                pool-pg_num:
                    type: Value
                    help: specify the pg_num in the pools
                    default: 128

                pool-pgp_num:
                    type: Value
                    help: specify the pg_num in the pools
                    default: 128

                pool-size:
                    type: Value
                    help: specify the size (replicas) set for the pools
                    default: 3

                pool-min_size:
                    type: Value
                    help: specify the minimum size (replicas) set for the pools
                    default: 2

          - title: Ceph clients
            options:
                check-clients:
                    type: Bool
                    help: Specify whether to run Ceph clients validation
                    default: True

                openstack-client-name:
                    type: Value
                    help: the name of the client set for the Openstack services
                    default: openstack