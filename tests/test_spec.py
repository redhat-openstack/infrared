import os

from cli import ngclg

default_settings_dir = "."


def test_yamls_file_locations(tmpdir):
    """
    Verify IR is looking for correct file locations.
    """
    subcommand = "virsh"

    # create mock settings structure
    app_dir = tmpdir.mkdir("installer")
    app_spec_dir = app_dir.mkdir(subcommand)
    file1 = app_dir.mkdir("arg1").mkdir("arg2").join("test_load2.yml")
    file2 = app_spec_dir.mkdir("arg1").mkdir("arg2").join("test_load1.yml")
    file1.write("""---
    network:
        ip: 1
    """)
    file2.write("""---
    network:
        ip: 2
    """)
    yaml_file_arg = ngclg.YamlFile(
        'arg1-arg2', [app_dir.strpath], "", subcommand)

    locations = yaml_file_arg.get_file_locations()

    assert len(locations) == 3
    assert locations[0] == file2.dirname
    assert locations[1] == file1.dirname
    assert locations[2] == os.getcwd()

    files = yaml_file_arg.get_allowed_values()

    assert len(files) == 2
    assert files[0] == os.path.basename(file2.strpath)
    assert files[1] == os.path.basename(file1.strpath)
