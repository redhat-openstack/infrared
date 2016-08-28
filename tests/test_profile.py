import py
import pytest

from cli import exceptions
from cli import profile_manager


@pytest.mark.parametrize('inventory_content', ["fake content", ""])
def test_profile_inventory(tmpdir, inventory_content, mock_spec):
    if inventory_content:
        myfile = tmpdir.mkdir("ir_dir").join("fake_hosts_file")
        myfile.write(inventory_content)
        org_inventory = myfile.strpath
    else:
        org_inventory = None
        inventory_content = profile_manager.LOCAL_HOSTS

    wkpsc_name = "profile_test"

    new_prf = profile_manager.ProfileManager.create(
        name=wkpsc_name,
        inventory=org_inventory)
    assert isinstance(new_prf, profile_manager.Profile)
    assert new_prf.name == wkpsc_name

    profile_inventory = py.path.local(new_prf.inventory)
    assert profile_inventory.check(file=1)
    assert inventory_content == profile_inventory.read()

    # assert that reusing the profile finds the original file
    reuse_prf = profile_manager.ProfileManager.get(
        name=wkpsc_name)
    assert new_prf.name == reuse_prf.name
    reuse_inventory = py.path.local(reuse_prf.inventory)
    assert reuse_inventory.check(file=1)
    assert reuse_inventory.samefile(profile_inventory)
    assert inventory_content == reuse_inventory.read()


def test_create_list_use_profile(mock_spec):
    wkpsc_name = "profile_test"

    with pytest.raises(exceptions.IRProfileMissing):
        profile_manager.ProfileManager.get(name=wkpsc_name)

    new_prf = profile_manager.ProfileManager.create(name=wkpsc_name)
    assert isinstance(new_prf, profile_manager.Profile)
    assert new_prf.name == wkpsc_name

    profile_manager.ProfileManager.create()

    dirlist = profile_manager.ProfileManager.list()
    assert wkpsc_name in dirlist
    assert len(dirlist) == 2
    with pytest.raises(exceptions.IRProfileExists):
        profile_manager.ProfileManager.create(name=wkpsc_name)

    assert profile_manager.ProfileManager.get(
        name=wkpsc_name).name == wkpsc_name


def test_active_profile(mock_spec):
    assert profile_manager.ProfileManager.get_active() is None

    wkpsc_name = "profile_test"

    first_prf = profile_manager.ProfileManager.create(name=wkpsc_name)
    assert first_prf.name == profile_manager.ProfileManager.get_active().name

    another_prf = profile_manager.ProfileManager.create()
    assert another_prf.name == profile_manager.ProfileManager.get_active().name

    active_prf = profile_manager.ProfileManager.set_active(first_prf.name)
    assert active_prf.name == profile_manager.ProfileManager.get_active().name
    assert first_prf.name == active_prf.name

    profile_manager.ProfileManager.delete(first_prf.name)
    assert profile_manager.ProfileManager.get_active() is None


@pytest.mark.parametrize(
    "input_args, output_args",
    [("list", "\n"),
     ("create test_profile", "Profile 'test_profile' created\n")]
)
def test_profile_cli(input_args, output_args, capsys, mock_spec):
    from cli.scripts import profile
    parsed = profile.parse_args(input_args.split())
    parsed.func(**vars(parsed))
    out, err = capsys.readouterr()
    assert out == output_args
