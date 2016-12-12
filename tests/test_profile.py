import os

import py
import pytest

from infrared.core.services.profiles import ProfileManager
from infrared.core.utils import exceptions


@pytest.fixture(scope="session")
def profile_manager_fixture(tmpdir_factory):
    """Sets the default profile direcotry to the temporary one. """

    temp_profile_dir = tmpdir_factory.mktemp('pmtest')
    return ProfileManager(str(temp_profile_dir))


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


def test_profile_remove(profile_manager_fixture, test_profile):
    """Verify profile can be removed. """

    profile_manager_fixture.activate(test_profile.name)
    profile_manager_fixture.delete(test_profile.name)
    assert not profile_manager_fixture.is_active(test_profile.name)
    assert not os.path.exists(test_profile.path)


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
