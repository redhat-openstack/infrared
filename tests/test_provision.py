import os

from cli import spec


def test_dynamic_topology(tmpdir):
    """
    Verifiesthe topology is dynamically constructed.
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
    app_path = os.path.join(root_dir.strpath, "..")

    spec.TopologyArgument.settings_dir = app_path
    topology_arg = spec.TopologyArgument("controller:10,compute:2")
    # process topology
    topology_arg.resolve_value("topology", {})

    topology = topology_arg.value
    assert 'controller' in topology
    assert 'compute' in topology
    assert 'ceph' not in topology
    assert topology['controller']['amount'] == 10
    assert topology['compute']['amount'] == 2
    assert topology['controller']['memory'] == 8192
    assert topology['compute']['memory'] == 1024
