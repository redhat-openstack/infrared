import os
import pytest

from cli import workspace
from cli import exceptions


def test_create_list_get_workspace(tmpdir):
    workspace.WorkspaceManager.workspacedir = tmpdir.mkdir(
        "workspaces").strpath
    wkpsc_name = "workspace_test"

    with pytest.raises(exceptions.IRWorspaceMissing):
        workspace.WorkspaceManager.get(name=wkpsc_name)

    new_wkspc = workspace.WorkspaceManager.create(name=wkpsc_name)
    assert isinstance(new_wkspc, workspace.Workspace)
    assert new_wkspc.name == wkpsc_name
    another_wkspc = workspace.WorkspaceManager.create()

    dirlist = workspace.WorkspaceManager.list()
    assert wkpsc_name in dirlist
    assert len(dirlist) == 2
    with pytest.raises(exceptions.IRWorspaceExists):
        workspace.WorkspaceManager.create(name=wkpsc_name)

    assert workspace.WorkspaceManager.get(name=wkpsc_name).name == wkpsc_name
