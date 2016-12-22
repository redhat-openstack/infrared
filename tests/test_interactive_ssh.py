import pytest

from infrared.core.utils import interactive_ssh as issh
from infrared.core.utils import exceptions
from infrared.core.services import profiles


@pytest.fixture(scope="session")
def profile_manager_fixture(tmpdir_factory):
    """Sets the default profile direcotry to the temporary one. """

    temp_profile_dir = tmpdir_factory.mktemp('pmtest')
    profile_manager = profiles.ProfileManager(str(temp_profile_dir))
    from infrared.core.services import CoreServices
    CoreServices.register_service("profile_manager", profile_manager)
    yield profile_manager


def test_parse_inventory(profile_manager_fixture, mocker):

    name = 'test_profile'
    test_profile = profile_manager_fixture.create(name)
    profile_manager_fixture.activate(test_profile.name)
    test_profile.inventory = "tests/example/test_ssh_inventory"

    mock_os = mocker.patch.object(issh, "os")
    issh.ssh_to_host("test_host")

    ssh_cmd_str = " ".join([
        "sshpass -p passwd ssh -i /some_key_path",
        " -o ForwardAgent=yes",
        "-o ServerAliveInterval=30",
        "-o ControlMaster=auto",
        "-o ControlPersist=30m",
        "-o StrictHostKeyChecking=no",
        "-o UserKnownHostsFile=/dev/null",
        "-o ProxyCommand=\"ssh",
        "-o StrictHostKeyChecking=no",
        "-o UserKnownHostsFile=/dev/null",
        "-W %h:%p -i /some_another_key_path ttest@tthost\"",
        " -p 33 test-user@0.0.0.0"
    ])

    mock_os.system.assert_called_with(ssh_cmd_str)
    if profile_manager_fixture.has_profile(name):
        profile_manager_fixture.delete(name)


def test_wrong_host_exception(profile_manager_fixture):

    name = 'test_profile'
    test_profile = profile_manager_fixture.create(name)
    profile_manager_fixture.activate(test_profile.name)
    test_profile.inventory = "tests/example/test_ssh_inventory"

    with pytest.raises(exceptions.IRSshException):
        issh.ssh_to_host("wrong_host")
    if profile_manager_fixture.has_profile(name):
        profile_manager_fixture.delete(name)


def test_wrong_connection_type_exception(profile_manager_fixture):

    name = 'test_profile'
    test_profile = profile_manager_fixture.create(name)
    profile_manager_fixture.activate(test_profile.name)
    test_profile.inventory = "tests/example/test_ssh_inventory"

    with pytest.raises(exceptions.IRSshException):
        issh.ssh_to_host("localhost")
    if profile_manager_fixture.has_profile(name):
        profile_manager_fixture.delete(name)
