import os

from cli import provision


def test_dynamic_topology(tmpdir):
    """
    Verifies the topology is dynamically constructed.
    """
    root_dir = tmpdir.mkdir("topology")
    controller_yml = root_dir.join("controller.yaml")
    compute_yml = root_dir.join("compute.yaml")
    ceph_yml = root_dir.join("ceph.yaml")
    controller_yml.write("""---
memory: 8192
os: linux
name: controller
""")
    compute_yml.write("""---
memory: 1024
os: rhel
name: compute
""")
    ceph_yml.write("""---
memory: 2048
os: fedora
name: ceph
""")
    # prepare config
    app_path = os.path.join(root_dir.strpath, "..")
    res_args = dict(topology="10_controller,2_compute")

    # process topology
    provision.process_topology_args(res_args, app_path)
    topology = res_args['topology']
    assert 'controller' in topology
    assert 'compute' in topology
    assert 'ceph' not in topology
    assert topology['controller']['amount'] == 10
    assert topology['compute']['amount'] == 2
    assert topology['controller']['memory'] == 8192
    assert topology['compute']['memory'] == 1024
