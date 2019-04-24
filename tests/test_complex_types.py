import os

import pytest

from infrared.core.cli import cli
from infrared.core.utils import exceptions


@pytest.mark.parametrize(
    "test_value,expected", [
        ("item1,item2", ["item1", "item2"]),
        ("item1", ["item1", ]),
        ("item1,item2,item3,", ["item1", "item2", "item3", ''])])
def test_list_value_resolve(list_value_type, test_value, expected):
    """
    Verifies the string value can be resolved to the list.
    """
    assert expected == list_value_type.resolve(test_value)


@pytest.mark.parametrize("input_value, expected_return", [
    (['k1=v1'], {'k1': 'v1'}),
    (['l1.s1.k1=v1'], {'l1': {'s1': {'k1': 'v1'}}}),
    ([' s1.k1=v1 '], {'s1': {'k1': 'v1'}}),
    (['s1.k1=v1', 's1.k2=v2', 's2.k3=v3'],
     {'s1': {'k1': 'v1', 'k2': 'v2'}, 's2': {'k3': 'v3'}}),
    ('k1=v1', {'k1': 'v1'}),
    ('s1.k1=v1', {'s1': {'k1': 'v1'}}),
    (' s1.k1=v1 ', {'s1': {'k1': 'v1'}}),
    ('s1.k1=v1,s1.k2=v2,s2.k3=v3',
     {'s1': {'k1': 'v1', 'k2': 'v2'}, 's2': {'k3': 'v3'}}),
    ('s1.k1=v1, s1.l2.k2=v2, s2.k3=v3',
     {'s1': {'k1': 'v1', 'l2': {'k2': 'v2'}}, 's2': {'k3': 'v3'}}),
])
def test_nested_dict_resolve(input_value, expected_return, nested_dict):
    """Verifies the return value of 'resolve' method in 'IniType' Complex type
    """
    assert nested_dict.resolve(input_value) == expected_return


@pytest.mark.parametrize("input_value, expected_return", [
    (['k1=v1'], {'k1': 'v1'}),
    (['l1.s1.k1=v1'], {'l1.s1.k1': 'v1'}),
    ([' s1.k1=v1 '], {'s1.k1': 'v1'}),
    (['s1.k1=v1', 's1.k2=v2', 's2.k3=v3'],
     {'s1.k1': 'v1', 's1.k2': 'v2', 's2.k3': 'v3'}),
    ('k1=v1', {'k1': 'v1'}),
])
def test_dict_type_resolve(input_value, expected_return, dict_type):
    """Verifies the return value of 'resolve' method in 'IniType' Complex type
    """
    assert dict_type.resolve(input_value) == expected_return


@pytest.mark.parametrize("input_value, expected_return", [
    ('test', True),
])
def test_flag_type_resolve(input_value, expected_return, flag_type):
    """Verifies the return value of 'resolve' method in 'Flag' Complex type
    """
    assert flag_type.resolve(input_value) == expected_return


@pytest.mark.parametrize('file_type', [cli.FileType], indirect=True)
def test_file_type_resolve(file_root_dir, file_type, monkeypatch):
    """Verifies the file complex type"""
    # change cwd to the temp dir
    monkeypatch.setattr("os.getcwd", lambda: file_root_dir.strpath)

    assert file_type.resolve('file1') == file_root_dir.join(
        'file1.yml').strpath
    assert file_type.resolve('file2') == file_root_dir.join(
        'arg/name/file2').strpath
    with pytest.raises(exceptions.IRFileNotFoundException):
        file_type.resolve('file.yml')


@pytest.mark.parametrize('file_type', [cli.VarFileType], indirect=True)
def test_var_file_type_resolve(file_root_dir, file_type, monkeypatch):
    """Verifies the file complex type"""
    # change cwd to the temp dir
    monkeypatch.setattr("os.getcwd", lambda: file_root_dir.strpath)

    assert file_type.resolve('file1') == file_root_dir.join(
        'file1.yml').strpath
    assert file_type.resolve(
        os.path.abspath('file1')) == file_root_dir.join('file1.yml').strpath
    assert file_type.resolve('file2') == file_root_dir.join(
        'arg/name/file2').strpath
    assert file_type.resolve('file.yml') == file_root_dir.join(
        'defaults/arg/name/file.yml').strpath
    assert file_type.resolve('file3') == file_root_dir.join(
        'vars/arg/name/file3.yml').strpath
    assert file_type.resolve('nested/file4.yml') == file_root_dir.join(
        'vars/arg/name/nested/file4.yml').strpath

    with pytest.raises(exceptions.IRFileNotFoundException):
        file_type.resolve('file5')


@pytest.mark.parametrize('file_type', [cli.ListFileType], indirect=True)
def test_list_of_var_files(file_root_dir, file_type, monkeypatch):
    """Verifies the list of files"""
    monkeypatch.setattr("os.getcwd", lambda: file_root_dir.strpath)

    assert file_type.resolve('file1') == [
        file_root_dir.join('file1.yml').strpath]
    assert file_type.resolve('file1,file2') == [
        file_root_dir.join('file1.yml').strpath,
        file_root_dir.join('arg/name/file2').strpath]
    assert file_type.resolve('file3.yml,vars/arg/name/file3') == [
        file_root_dir.join('vars/arg/name/file3.yml').strpath,
        file_root_dir.join('vars/arg/name/file3.yml').strpath]


@pytest.mark.parametrize('dir_type', [cli.VarDirType], indirect=True)
def test_dir_type_resolve(dir_root_dir, dir_type, monkeypatch):
    """Verifies the file complex type"""
    # change cwd to the temp dir
    monkeypatch.setattr("os.getcwd", lambda: dir_root_dir.strpath)

    assert dir_type.resolve('dir0') == dir_root_dir.join(
        'dir0/').strpath
    assert dir_type.resolve('dir1') == dir_root_dir.join(
        'arg/name/dir1/').strpath
    assert dir_type.resolve('dir2') == dir_root_dir.join(
        'vars/arg/name/dir2/').strpath
    assert dir_type.resolve('dir3') == dir_root_dir.join(
        'defaults/arg/name/dir3/').strpath
    with pytest.raises(exceptions.IRFileNotFoundException):
        dir_type.resolve('dir4')


def list_of_file_names(settings_dirs, spec_option):
    """Create a new IniType complex type
    """
    return cli.ListOfFileNames("ListOfFileNames", settings_dirs, None,
                               spec_option)


def test_list_of_file_names_values_auto_propagation():
    expected = ["task1", "task2", "task3"]
    settings_dirs = ["", "", 'tests/example']
    spec_option = {'lookup_dir': 'post_tasks'}

    complex_action = list_of_file_names(settings_dirs, spec_option)
    allowed_values = complex_action.get_allowed_values()

    assert expected.sort() == allowed_values.sort()


def test_list_of_file_names_resolve():
    expected = ["task2", "task3"]
    settings_dirs = ["", "", 'tests/example/']
    spec_option = {'lookup_dir': 'post_tasks'}
    value = "task2,task3"

    complex_action = list_of_file_names(settings_dirs, spec_option)
    values = complex_action.resolve(value)

    assert expected.sort() == values.sort()
