import os
import py
import pytest
from cli import exceptions
from cli import workspace


def test_create_list_use_workspace(tmpdir):
    org_inventory = tmpdir.mkdir("ir_dir").join("hosts")
    inventory_content = "fake content"
    org_inventory.write(inventory_content)

    workspace.WorkspaceManager.workspacedir = tmpdir.mkdir(
        "workspaces").strpath
    wkpsc_name = "workspace_test"

    with pytest.raises(exceptions.IRWorkspaceMissing):
        workspace.WorkspaceManager.use(name=wkpsc_name)

    new_wkspc = workspace.WorkspaceManager.create(name=wkpsc_name,
                                                  inventory=org_inventory)
    assert isinstance(new_wkspc, workspace.Workspace)
    assert new_wkspc.name == wkpsc_name
    # assert org_inventory.check(link=1, file=1)
    assert inventory_content == py.path.local(os.path.join(new_wkspc.path,
                                                           "hosts")).read()
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

