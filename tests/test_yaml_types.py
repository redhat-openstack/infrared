import os
import pytest

from infrared.core.cli import cli

default_settings_dir = "."
subcommand = "virsh"


@pytest.fixture(scope='function')
def spec_app(tmpdir):
    """
    Creates a temporary file structure file.
    """

    # create mock settings structure
    app_dir = tmpdir.mkdir("installer")
    app_spec_dir = app_dir.mkdir(subcommand)

    return dict(app_dir=app_dir, app_spec_dir=app_spec_dir)


def test_yamls_file_locations(spec_app):
    """
    Verify IR is looking for correct file locations.
    """

    file1 = spec_app['app_dir'].mkdir("arg1").mkdir("arg2").join(
        "test_load2.yml")
    file2 = spec_app['app_spec_dir'].mkdir("arg1").mkdir("arg2").join(
        "test_load1.yml")
    file1.write("""---
    network:
        ip: 1
    """)
    file2.write("""---
    network:
        ip: 2
    """)
    yaml_file_arg = cli.YamlFile(
        'arg1-arg2', [spec_app['app_dir'].strpath], "", "", subcommand)

    locations = yaml_file_arg.get_file_locations()

    assert len(locations) == 3
    assert locations[0] == file2.dirname
    assert locations[1] == file1.dirname
    assert locations[2] == os.getcwd()

    files = yaml_file_arg.get_allowed_values()

    assert len(files) == 2
    assert files[0] == os.path.basename(file2.strpath)
    assert files[1] == os.path.basename(file1.strpath)


def test_yaml_list(spec_app):
    """
    Verify list of yamls type.
    """

    file1 = spec_app['app_dir'].mkdir("arg1").mkdir("arg2").join(
        "item1.yml")
    file2 = spec_app['app_spec_dir'].mkdir("arg1").mkdir("arg2").join(
        "item2.yml")
    file1.write("""---
    network:
        ip: 1
    """)
    file2.write("""---
    network:
        ip: 2
    """)
    yaml_file_arg = cli.ListOfYamls(
        'arg1-arg2', [spec_app['app_dir'].strpath], "", '', subcommand)

    locations = yaml_file_arg.get_file_locations()

    assert len(locations) == 3
    assert locations[0] == file2.dirname
    assert locations[1] == file1.dirname
    assert locations[2] == os.getcwd()

    files = yaml_file_arg.get_allowed_values()

    assert len(files) == 2
    assert files[0] == file2.purebasename
    assert files[1] == file1.purebasename

    value = yaml_file_arg.resolve('item1,item2')

    assert "item1" in value
    assert value['item1']['network']['ip'] == 1
    assert "item2" in value
    assert value['item2']['network']['ip'] == 2
