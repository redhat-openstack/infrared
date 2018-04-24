import pytest

from infrared.core.utils import interactive_ssh as issh
from infrared.core.utils import exceptions
from infrared.core.services import workspaces


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
    test_workspace = workspace_manager_fixture.create(name)
    workspace_manager_fixture.activate(test_workspace.name)
    test_workspace.inventory = "tests/example/test_ssh_inventory"
    yield test_workspace
    if workspace_manager_fixture.has_workspace(name):
        workspace_manager_fixture.delete(name)


def test_parse_inventory(workspace_manager_fixture, test_workspace, mocker):
    import os
    mocker.patch("os.system")

    ssh_cmd_str = " ".join([
        "ssh -i /dev/null",
        " -o ForwardAgent=yes",
        "-o ServerAliveInterval=30",
        "-o ControlMaster=auto",
        "-o ControlPersist=30m",
        "-o StrictHostKeyChecking=no",
        "-o UserKnownHostsFile=/dev/null",
        "-o ProxyCommand=\"ssh",
        "-o StrictHostKeyChecking=no",
        "-o UserKnownHostsFile=/dev/null",
        "-W %h:%p -i /dev/null ttest@tthost\"",
        " -p 33 -t test-user@0.0.0.0"
    ])

    issh.ssh_to_host("test_host")

    # make sure we aren't calling ssh more than once
    os.system.assert_called_once_with(ssh_cmd_str)

    ssh_cmd_str = " ".join([
        "ssh -i /dev/null",
        " -o ForwardAgent=yes",
        "-o ServerAliveInterval=30",
        "-o ControlMaster=auto",
        "-o ControlPersist=30m",
        "-o StrictHostKeyChecking=no",
        "-o UserKnownHostsFile=/dev/null",
        "-o ProxyCommand=\"ssh",
        "-o StrictHostKeyChecking=no",
        "-o UserKnownHostsFile=/dev/null",
        "-W %h:%p -i /dev/null ttest@tthost\"",
        " -p 33 -t test-user@0.0.0.0 \"some cmd line\""
    ])

    issh.ssh_to_host("test_host", "some cmd line")

    os.system.assert_called_with(ssh_cmd_str)


def test_wrong_host_exception(workspace_manager_fixture, test_workspace):

    with pytest.raises(exceptions.IRSshException):
        issh.ssh_to_host("wrong_host")


def test_wrong_connection_type_exception(workspace_manager_fixture,
                                         test_workspace):

    with pytest.raises(exceptions.IRSshException):
        issh.ssh_to_host("localhost")
