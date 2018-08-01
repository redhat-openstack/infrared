import os

import py
import pytest

from infrared.core.services import workspaces
from infrared.core.utils import exceptions


@pytest.fixture(scope="session")
def workspace_manager_fixture(tmpdir_factory):
    """Sets the default workspace direcotry to the temporary one. """

    temp_workspace_dir = tmpdir_factory.mktemp('pmtest')
    workspace_manager = workspaces.WorkspaceManager(str(temp_workspace_dir))
    from infrared.core.services import CoreServices
    CoreServices.register_service("workspace_manager", workspace_manager)
    yield workspace_manager


@pytest.fixture()
def test_workspace(workspace_manager_fixture):
    """Creates test workspace in the temp directory. """

    name = 'test_workspace'
    yield workspace_manager_fixture.create(name)
    if workspace_manager_fixture.has_workspace(name):
        workspace_manager_fixture.delete(name)


@pytest.mark.parametrize('name', ["test_wspc", None])
def test_workspace_create(workspace_manager_fixture, name):
    """Verify Workspace manager allows to create a new workspace. """

    workspace = workspace_manager_fixture.create(name)
    assert os.path.isdir(workspace.path)
    if name:
        assert workspace.name == name


def test_workspace_activate(workspace_manager_fixture, test_workspace):
    """Verify Workspace manager allows to activate a workspace. """

    workspace_manager_fixture.activate(test_workspace.name)
    assert workspace_manager_fixture.is_active(test_workspace.name)
    workspace = workspace_manager_fixture.get_active_workspace()
    assert workspace.name == test_workspace.name
    assert workspace.path == test_workspace.path


def test_workspace_activate_negative(workspace_manager_fixture):
    """Verify Workspace manager allows to activate a workspace. """

    with pytest.raises(exceptions.IRWorkspaceMissing):
        workspace_manager_fixture.activate("wrong_workspace")


def test_active_workspace_from_env(workspace_manager_fixture, test_workspace):
    """Verify that active workspace from env"""

    twspc_name = test_workspace.name

    assert workspace_manager_fixture.get_active_workspace() is None
    try:
        os.environ[workspaces.ACTIVE_WORKSPACE_ENV_NAME] = test_workspace.name
        assert workspace_manager_fixture.get_active_workspace(). \
            name == twspc_name
    finally:
        os.environ.pop(workspaces.ACTIVE_WORKSPACE_ENV_NAME)

    workspace_manager_fixture.create("new_workspace")
    workspace_manager_fixture.activate("new_workspace")
    assert workspace_manager_fixture.get_active_workspace(). \
        name == "new_workspace"

    try:
        os.environ[workspaces.ACTIVE_WORKSPACE_ENV_NAME] = test_workspace.name
        assert workspace_manager_fixture.get_active_workspace(). \
            name == twspc_name
    finally:
        os.environ.pop(workspaces.ACTIVE_WORKSPACE_ENV_NAME)


def test_activate_workspace_env_exception(workspace_manager_fixture,
                                          test_workspace):

    try:
        os.environ[workspaces.ACTIVE_WORKSPACE_ENV_NAME] = test_workspace.name
        with pytest.raises(exceptions.IRException):
            workspace_manager_fixture.activate(test_workspace.name)
    finally:
        os.environ.pop(workspaces.ACTIVE_WORKSPACE_ENV_NAME)


def test_workspace_remove(workspace_manager_fixture, test_workspace):
    """Verify workspace can be removed. """

    workspace_manager_fixture.activate(test_workspace.name)
    workspace_manager_fixture.delete(test_workspace.name)
    assert not workspace_manager_fixture.is_active(test_workspace.name)
    assert not os.path.exists(test_workspace.path)


def test_workspace_user_inventory(workspace_manager_fixture, test_workspace,
                                  tmpdir):
    """Verify workspace inventory can be updated. """

    inventory_symlink = test_workspace.inventory

    inventory_file = os.path.realpath(test_workspace.inventory)
    assert os.path.basename(inventory_file) == "local_hosts"

    myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    myfile.write("fake_content")
    test_workspace.inventory = str(myfile)

    # assert symlink is the same file
    assert inventory_symlink == test_workspace.inventory
    inventory_file = os.path.realpath(test_workspace.inventory)
    # assert target is the new file, copied to workspace dir
    assert os.path.dirname(inventory_file) == test_workspace.path
    assert os.path.basename(inventory_file) == myfile.basename


def test_workspace_inventory_setter(workspace_manager_fixture, test_workspace,
                                    tmpdir):
    """Verify workspace inventory can be set

    Without calling getter first.
    """

    myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    myfile.write("fake_content")
    test_workspace.inventory = str(myfile)

    inventory_file = os.path.realpath(test_workspace.inventory)
    # assert target is the new file, copied to workspace dir
    assert os.path.dirname(inventory_file) == test_workspace.path
    assert os.path.basename(inventory_file) == myfile.basename


def test_workspace_fetch_inventory(workspace_manager_fixture, test_workspace):
    """Verify workspace inventory returns path to workspace link. """

    inventory_path = test_workspace.inventory

    # assert result is in workspace dir (abs path
    assert os.path.dirname(inventory_path) == os.path.abspath(
        test_workspace.path)
    # assert result is "hosts" symlink
    assert os.path.islink(inventory_path)
    assert os.path.basename(inventory_path) == "hosts"


def test_copy_outside_keys(test_workspace, mocker):
    path = test_workspace.path
    test_inv = os.path.join(path, "new_test_env")

    tkey_file = "/tmp/id_rsa_tkey"
    with open(tkey_file, "w") as tkey:
        tkey.write("test ssh key stub")
    with open(test_inv, "w") as new_inv:
        new_inv.write("hypervisor ansible_ssh_private_key_file={key}\n"
                      "host-0 {key}\n"
                      "host-1 id_rsa".format(key=tkey_file))
    mocker.patch('tempfile._get_candidate_names',
                 return_value=iter(["zzzzz"]))
    test_workspace.inventory = test_inv
    test_workspace._copy_outside_keys()
    with open(test_inv, "r") as inv:
        assert inv.read() == (
            "hypervisor ansible_ssh_private_key_file={key}\n"
            "host-0 {key}\n"
            "host-1 id_rsa").format(key=os.path.join(
                test_workspace.path_placeholder, "id_rsa_tkey-zzzzz"))

    assert "id_rsa_tkey-zzzzz" in os.listdir(test_workspace.path)


@pytest.mark.parametrize('inventory_content', ["fake content", ""])
def test_workspace_copy_file(workspace_manager_fixture, test_workspace,
                             tmpdir, inventory_content):
    """Verify file can be copied to the workspace. """

    myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    myfile.write(inventory_content)
    org_inventory = myfile.strpath

    target_path = test_workspace.copy_file(org_inventory)
    assert target_path == os.path.join(
        test_workspace.path, os.path.basename(org_inventory))

    workspace_inventory = py.path.local(target_path)
    assert workspace_inventory.check(file=1)
    assert inventory_content == workspace_inventory.read()


@pytest.mark.parametrize('inventory_content', ["fake content", ])
def test_workspace_link_file(workspace_manager_fixture, test_workspace,
                             tmpdir, inventory_content):
    """Verify workspaces allows to add a link to a file. """

    myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    myfile.write(inventory_content)
    org_inventory = myfile.strpath

    target_path = test_workspace.link_file(org_inventory)
    assert target_path == os.path.join(
        test_workspace.path, os.path.basename(org_inventory))
    workspace_inventory = py.path.local(target_path)
    assert workspace_inventory.islink()
    assert inventory_content == workspace_inventory.read()


@pytest.mark.parametrize('workspace_name', ["new_test_workspace", None])
def test_workspace_import(workspace_manager_fixture, test_workspace,
                          workspace_name, tmpdir):
    """Test export/import

    1. tests control over imported name
    2. tests original workspace paths are removed from new workspace
    3. tests original workspace inventory isn't changed
    4. tests metadata file not in new workspace
    """

    cwd = os.getcwd()
    os.chdir(tmpdir.strpath)

    myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    myfile.write(test_workspace.path)
    test_workspace.inventory = str(myfile)

    workspace_manager_fixture.export_workspace(test_workspace.name, "test_boo")
    workspace_manager_fixture.import_workspace("test_boo.tgz", workspace_name)

    assert workspace_manager_fixture.get(workspace_name or "test_boo")

    active_workspace = workspace_manager_fixture.get_active_workspace()
    assert active_workspace.name == workspace_name or "test_boo"

    old_inv_file = os.path.join(os.path.dirname(test_workspace.inventory),
                                os.readlink(test_workspace.inventory))
    with open(old_inv_file, "r") as old_inv:
        old_inv_text = old_inv.read()
        assert test_workspace.path in old_inv_text
        assert active_workspace.path not in old_inv_text

    new_inv_file = os.path.join(os.path.dirname(active_workspace.inventory),
                                os.readlink(active_workspace.inventory))
    with open(new_inv_file, "r") as new_inv:
        new_inv_text = new_inv.read()
        assert test_workspace.path not in new_inv_text
        assert active_workspace.path in new_inv_text

    os.chdir(cwd)


def test_workspace_import_no_file(workspace_manager_fixture):
    with pytest.raises(exceptions.IRFailedToImportWorkspace):
        workspace_manager_fixture.import_workspace("zoooo.tgz", None)


def test_workspace_import_workspace_exists(workspace_manager_fixture, mocker):
    twspc = workspace_manager_fixture.create("new_t_wspc")
    workspace_manager_fixture.activate(twspc.name)
    mock_os = mocker.patch.object(workspaces, "os")
    mock_os.path.exists.return_value = True
    back_get = workspace_manager_fixture.get
    workspace_manager_fixture.get = lambda x: test_workspace

    try:
        with pytest.raises(exceptions.IRWorkspaceExists):
            workspace_manager_fixture.import_workspace("zoooo.tgz", twspc.name)
    finally:
        workspace_manager_fixture.get = back_get


def test_workspace_export(workspace_manager_fixture, test_workspace, tmpdir):
    cwd = os.getcwd()

    os.chdir(tmpdir.strpath)

    back_get = workspace_manager_fixture.get
    workspace_manager_fixture.get = lambda x: test_workspace
    workspace_manager_fixture.export_workspace(test_workspace.name,
                                               "some_file")
    workspace_manager_fixture.get = back_get

    assert os.path.exists("some_file.tgz")
    os.remove("some_file.tgz")

    back_get = workspace_manager_fixture.get
    workspace_manager_fixture.get = lambda x: test_workspace
    workspace_manager_fixture.export_workspace(test_workspace.name)
    workspace_manager_fixture.get = back_get
    assert os.path.exists("{}.tgz".format(test_workspace.name))
    os.remove("{}.tgz".format(test_workspace.name))

    back_get = workspace_manager_fixture.get
    workspace_manager_fixture.activate(test_workspace.name)
    workspace_manager_fixture.get = lambda x: test_workspace
    workspace_manager_fixture.export_workspace(None)
    workspace_manager_fixture.get = back_get
    assert os.path.exists("{}.tgz".format(test_workspace.name))

    os.chdir(cwd)


def test_workspace_export_not_excists(workspace_manager_fixture):
    with pytest.raises(exceptions.IRWorkspaceMissing):
        workspace_manager_fixture.export_workspace("some_workspace")


def test_workspace_export_no_active(workspace_manager_fixture, test_workspace):
    with pytest.raises(exceptions.IRNoActiveWorkspaceFound):
        workspace_manager_fixture.export_workspace(None)


def test_workspace_node_list(workspace_manager_fixture, test_workspace):
    workspace_manager_fixture.activate(test_workspace.name)
    test_boo = workspace_manager_fixture.create("test_list_wspc")
    test_boo.inventory = "tests/example/test_ssh_inventory"

    # active workspace
    node_lst = workspace_manager_fixture.node_list()
    assert node_lst == []

    # not active workspace
    node_lst_boo = workspace_manager_fixture.node_list(
        workspace_name="test_list_wspc")
    assert node_lst_boo == [("test_host", "0.0.0.0", "test_group")]


def test_workspace_node_list_errors(workspace_manager_fixture):
    with pytest.raises(exceptions.IRNoActiveWorkspaceFound):
        workspace_manager_fixture.node_list()

    with pytest.raises(exceptions.IRWorkspaceMissing):
        workspace_manager_fixture.node_list("strange_workspace")


def test_workspace_group_list(workspace_manager_fixture, test_workspace):
    workspace_manager_fixture.activate(test_workspace.name)
    test_boo = workspace_manager_fixture.create("test_group_wspc")
    test_boo.inventory = "tests/example/test_ssh_inventory"

    # active workspace
    group_lst = workspace_manager_fixture.group_list()
    assert group_lst == []

    # not active workspace
    group_lst_boo = workspace_manager_fixture.group_list(
        workspace_name="test_group_wspc")
    test_groups = [('test_group', 'test_host')]
    assert group_lst_boo == test_groups
