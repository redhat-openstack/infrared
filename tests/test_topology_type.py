from infrared.core.cli import cli


def test_dynamic_topology(tmpdir):
    """
    Verifies the topology is dynamically constructed.
    """
    root_dir = tmpdir.mkdir("topology")
    controller_yml = root_dir.join("controller.yml")
    compute_yml = root_dir.join("compute.yml")
    ceph_yml = root_dir.join("ceph.yml")
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

    topology_arg = cli.Topology('topology', [tmpdir.strpath], '', '', '')
    # process topology
    topology = topology_arg.resolve("controller:10,compute:2")

    assert 'controller' in topology
    assert 'compute' in topology
    assert 'ceph' not in topology
    assert topology['controller']['amount'] == 10
    assert topology['compute']['amount'] == 2
    assert topology['controller']['memory'] == 8192
    assert topology['compute']['memory'] == 1024
