import os

import py
import pytest

from infrared.core.services import profiles
from infrared.core.utils import exceptions


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
    yield profile_manager_fixture.create(name)
    if profile_manager_fixture.has_profile(name):
        profile_manager_fixture.delete(name)


@pytest.mark.parametrize('name', ["test_prof", None])
def test_profile_create(profile_manager_fixture, name):
    """Verify Profile manager allows to create a new profile. """

    profile = profile_manager_fixture.create(name)
    assert os.path.isdir(profile.path)
    if name:
        assert profile.name == name


def test_profile_activate(profile_manager_fixture, test_profile):
    """Verify Profile manager allows to activate a profile. """

    profile_manager_fixture.activate(test_profile.name)
    assert profile_manager_fixture.is_active(test_profile.name)
    profile = profile_manager_fixture.get_active_profile()
    assert profile.name == test_profile.name
    assert profile.path == test_profile.path


def test_profile_activate_negative(profile_manager_fixture):
    """Verify Profile manager allows to activate a profile. """

    with pytest.raises(exceptions.IRProfileMissing):
        profile_manager_fixture.activate("wrong_profile")


def test_active_profile_from_env(profile_manager_fixture, test_profile):
    """Verify that active profile from env"""

    tprof_name = test_profile.name

    assert profile_manager_fixture.get_active_profile() is None
    os.environ[profiles.ACTIVE_PROFILE_ENV_NAME] = test_profile.name
    assert profile_manager_fixture.get_active_profile().name == tprof_name
    os.environ.pop(profiles.ACTIVE_PROFILE_ENV_NAME)

    profile_manager_fixture.create("new_profile")
    profile_manager_fixture.activate("new_profile")
    assert profile_manager_fixture.get_active_profile().name == "new_profile"

    os.environ[profiles.ACTIVE_PROFILE_ENV_NAME] = test_profile.name
    assert profile_manager_fixture.get_active_profile().name == tprof_name
    os.environ.pop(profiles.ACTIVE_PROFILE_ENV_NAME)


def test_activate_profile_env_exception(profile_manager_fixture, test_profile):

    os.environ[profiles.ACTIVE_PROFILE_ENV_NAME] = test_profile.name
    with pytest.raises(exceptions.IRException):
        profile_manager_fixture.activate(test_profile.name)
    os.environ.pop(profiles.ACTIVE_PROFILE_ENV_NAME)


def test_profile_remove(profile_manager_fixture, test_profile):
    """Verify profile can be removed. """

    profile_manager_fixture.activate(test_profile.name)
    profile_manager_fixture.delete(test_profile.name)
    assert not profile_manager_fixture.is_active(test_profile.name)
    assert not os.path.exists(test_profile.path)


def test_profile_user_inventory(profile_manager_fixture, test_profile, tmpdir):
    """Verify profile inventory can be updated. """

    inventory_symlink = test_profile.inventory

    inventory_file = os.path.realpath(test_profile.inventory)
    assert os.path.basename(inventory_file) == "local_hosts"

    myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    myfile.write("fake_content")
    test_profile.inventory = str(myfile)

    # assert symlink is the same file
    assert inventory_symlink == test_profile.inventory
    inventory_file = os.path.realpath(test_profile.inventory)
    # assert target is the new file, copied to profile dir
    assert os.path.dirname(inventory_file) == test_profile.path
    assert os.path.basename(inventory_file) == myfile.basename


def test_profile_inventory_setter(profile_manager_fixture, test_profile,
                                  tmpdir):
    """Verify profile inventory can be set

    Without calling getter first.
    """

    myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    myfile.write("fake_content")
    test_profile.inventory = str(myfile)

    inventory_file = os.path.realpath(test_profile.inventory)
    # assert target is the new file, copied to profile dir
    assert os.path.dirname(inventory_file) == test_profile.path
    assert os.path.basename(inventory_file) == myfile.basename


@pytest.mark.parametrize('inventory_content', ["fake content", ""])
def test_profile_copy_file(profile_manager_fixture, test_profile,
                           tmpdir, inventory_content):
    """Verify file can be copied to the profile. """

    myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    myfile.write(inventory_content)
    org_inventory = myfile.strpath

    target_path = test_profile.copy_file(org_inventory)
    assert target_path == os.path.join(
        test_profile.path, os.path.basename(org_inventory))

    profile_inventory = py.path.local(target_path)
    assert profile_inventory.check(file=1)
    assert inventory_content == profile_inventory.read()


@pytest.mark.parametrize('inventory_content', ["fake content", ])
def test_profile_link_file(profile_manager_fixture, test_profile,
                           tmpdir, inventory_content):
    """Verify profiles allows to add a link to a file. """

    myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
    myfile.write(inventory_content)
    org_inventory = myfile.strpath

    target_path = test_profile.link_file(org_inventory)
    assert target_path == os.path.join(
        test_profile.path, os.path.basename(org_inventory))
    profile_inventory = py.path.local(target_path)
    assert profile_inventory.islink()
    assert inventory_content == profile_inventory.read()


@pytest.mark.parametrize('profile_name', ["new_test_profile", None])
def test_profile_import(profile_manager_fixture, test_profile, profile_name,
                        tmpdir):

    cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    profile_manager_fixture.export_profile(test_profile.name, "test_boo")

    profile_manager_fixture.import_profile("test_boo.tgz", profile_name)

    if profile_name is None:
        assert profile_manager_fixture.get("test_boo")
    else:
        assert profile_manager_fixture.get(profile_name)

    os.chdir(cwd)


def test_profile_import_no_file(profile_manager_fixture):
    with pytest.raises(IOError):
        profile_manager_fixture.import_profile("zooooo.tgz", None)


def test_profile_import_profile_exists(profile_manager_fixture, mocker):
    tprof = profile_manager_fixture.create("new_t_prof")
    profile_manager_fixture.activate(tprof.name)
    mock_os = mocker.patch.object(profiles, "os")
    mock_os.path.exists.return_value = True
    back_get = profile_manager_fixture.get
    profile_manager_fixture.get = lambda x: test_profile
    with pytest.raises(exceptions.IRProfileExists):
        profile_manager_fixture.import_profile("zooooo.tgz", tprof.name)

    profile_manager_fixture.get = back_get


def test_profile_export(profile_manager_fixture, test_profile, tmpdir):
    cwd = os.getcwd()

    os.chdir(tmpdir.strpath)

    back_get = profile_manager_fixture.get
    profile_manager_fixture.get = lambda x: test_profile
    profile_manager_fixture.export_profile(test_profile.name, "some_file")
    profile_manager_fixture.get = back_get

    assert os.path.exists("some_file.tgz")
    os.remove("some_file.tgz")

    back_get = profile_manager_fixture.get
    profile_manager_fixture.get = lambda x: test_profile
    profile_manager_fixture.export_profile(test_profile.name)
    profile_manager_fixture.get = back_get
    assert os.path.exists("{}.tgz".format(test_profile.name))
    os.remove("{}.tgz".format(test_profile.name))

    back_get = profile_manager_fixture.get
    profile_manager_fixture.activate(test_profile.name)
    profile_manager_fixture.get = lambda x: test_profile
    profile_manager_fixture.export_profile(None)
    profile_manager_fixture.get = back_get
    assert os.path.exists("{}.tgz".format(test_profile.name))

    os.chdir(cwd)


def test_profile_export_not_excists(profile_manager_fixture):
    with pytest.raises(exceptions.IRProfileMissing):
        profile_manager_fixture.export_profile("some_profile")


def test_profile_export_no_active(profile_manager_fixture, test_profile):
    with pytest.raises(exceptions.IRNoActiveProfileFound):
        profile_manager_fixture.export_profile(None)


def test_profile_node_list(profile_manager_fixture, test_profile):
    profile_manager_fixture.activate(test_profile.name)
    test_boo = profile_manager_fixture.create("test_list_prof")
    test_boo.inventory = "tests/example/test_ssh_inventory"

    # active profile
    node_lst = profile_manager_fixture.node_list()
    assert node_lst == []

    # not active profile
    node_lst_boo = profile_manager_fixture.node_list(
        profile_name="test_list_prof")
    assert node_lst_boo == [("test_host", "0.0.0.0")]


def test_profile_node_list_errors(profile_manager_fixture):
    with pytest.raises(exceptions.IRNoActiveProfileFound):
        profile_manager_fixture.node_list()

    with pytest.raises(exceptions.IRProfileMissing):
        profile_manager_fixture.node_list("strange_profile")
