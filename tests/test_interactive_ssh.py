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


@pytest.fixture()
def test_profile(profile_manager_fixture):
    """Creates test profile in the temp directory. """

    name = 'test_profile'
    test_profile = profile_manager_fixture.create(name)
    profile_manager_fixture.activate(test_profile.name)
    test_profile.inventory = "tests/example/test_ssh_inventory"
    yield test_profile
    if profile_manager_fixture.has_profile(name):
        profile_manager_fixture.delete(name)


def test_parse_inventory(profile_manager_fixture, test_profile, mocker):

    mock_os = mocker.patch.object(issh, "os")
    issh.ssh_to_host("test_host")

    ssh_cmd_str = " ".join([
        "ssh -i /some_key_path",
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


def test_wrong_host_exception(profile_manager_fixture, test_profile):

    with pytest.raises(exceptions.IRSshException):
        issh.ssh_to_host("wrong_host")


def test_wrong_connection_type_exception(profile_manager_fixture,
                                         test_profile):

    with pytest.raises(exceptions.IRSshException):
        issh.ssh_to_host("localhost")
