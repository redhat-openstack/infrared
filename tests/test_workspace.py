import py
import pytest
from cli import exceptions
from cli import workspace


@pytest.mark.parametrize('inventory_content', ["fake content", ""])
def test_workspace_inventory(tmpdir, inventory_content):
    if inventory_content:
        myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
        myfile.write(inventory_content)
        org_inventory = myfile.strpath
    else:
        org_inventory = None
        inventory_content = workspace.LOCAL_HOSTS

    workspace.WorkspaceManager.workspacedir = tmpdir.mkdir(
        "workspaces").strpath
    wkpsc_name = "workspace_test"

    new_wkspc = workspace.WorkspaceManager.create(
        name=wkpsc_name,
        inventory=org_inventory)
    assert isinstance(new_wkspc, workspace.Workspace)
    assert new_wkspc.name == wkpsc_name

    workspace_inventory = py.path.local(new_wkspc.inventory)
    assert workspace_inventory.check(file=1)
    assert inventory_content == workspace_inventory.read()

    # assert that reusing the workspace finds the original file
    reuse_wkspc = workspace.WorkspaceManager.get(
        name=wkpsc_name)
    assert new_wkspc.name == reuse_wkspc.name
    reuse_inventory = py.path.local(reuse_wkspc.inventory)
    assert reuse_inventory.check(file=1)
    assert reuse_inventory.samefile(workspace_inventory)
    assert inventory_content == reuse_inventory.read()


def test_create_list_use_workspace(tmpdir):
    workspace.WorkspaceManager.workspacedir = tmpdir.mkdir(
        "workspaces").strpath
    wkpsc_name = "workspace_test"

    with pytest.raises(exceptions.IRWorkspaceMissing):
        workspace.WorkspaceManager.use(name=wkpsc_name)

    new_wkspc = workspace.WorkspaceManager.create(name=wkpsc_name)
    assert isinstance(new_wkspc, workspace.Workspace)
    assert new_wkspc.name == wkpsc_name
    _another_wkspc = workspace.WorkspaceManager.create()

    dirlist = workspace.WorkspaceManager.list()
    assert wkpsc_name in dirlist
    assert len(dirlist) == 2
    with pytest.raises(exceptions.IRWorkspaceExists):
        workspace.WorkspaceManager.create(name=wkpsc_name)

    assert workspace.WorkspaceManager.use(name=wkpsc_name).name == wkpsc_name


def test_get_workspace(tmpdir):
    workspace.WorkspaceManager.workspacedir = tmpdir.mkdir(
        "workspaces").strpath
    wkpsc_name = "workspace_test"

    new_wkspc = workspace.WorkspaceManager.get(name=wkpsc_name)
    assert isinstance(new_wkspc, workspace.Workspace)
    assert new_wkspc.name == wkpsc_name

    reuse_wkspc = workspace.WorkspaceManager.get(name=wkpsc_name)
    assert isinstance(reuse_wkspc, workspace.Workspace)
    assert new_wkspc.name == reuse_wkspc.name

    dirlist = workspace.WorkspaceManager.list()
    assert wkpsc_name in dirlist
    assert len(dirlist) == 1

