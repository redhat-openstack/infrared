import pytest

from infrared.core.utils import interactive_ssh as issh
from infrared.core.utils import exceptions


def test_parse_inventory(
        workspace_manager_fixture, test_workspace_ssh, mocker):
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


def test_wrong_host_exception(workspace_manager_fixture, test_workspace_ssh):

    with pytest.raises(exceptions.IRSshException):
        issh.ssh_to_host("wrong_host")


def test_wrong_connection_type_exception(workspace_manager_fixture,
                                         test_workspace_ssh):

    with pytest.raises(exceptions.IRSshException):
        issh.ssh_to_host("localhost")
