import os

import pytest

from infrared.core.cli import cli
from infrared.core.utils import exceptions


@pytest.fixture
def list_value_type():
    """
    Create a new list value complex type
    """
    return cli.ListValue("test", [os.getcwd(), ], 'cmd')


@pytest.fixture
def ini_type():
    """Create a new IniType complex type
    """
    return cli.IniType("TestIniType", None, None)


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
    (['k1=v1'], {'defaults': {'k1': 'v1'}}),
    (['s1.k1=v1'], {'s1': {'k1': 'v1'}}),
    ([' s1.k1=v1 '], {'s1': {'k1': 'v1'}}),
    (['s1.k1=v1', 's1.k2=v2', 's2.k3=v3'],
     {'s1': {'k1': 'v1', 'k2': 'v2'}, 's2': {'k3': 'v3'}}),
    ('k1=v1', {'defaults': {'k1': 'v1'}}),
    ('s1.k1=v1', {'s1': {'k1': 'v1'}}),
    (' s1.k1=v1 ', {'s1': {'k1': 'v1'}}),
    ('s1.k1=v1,s1.k2=v2,s2.k3=v3',
     {'s1': {'k1': 'v1', 'k2': 'v2'}, 's2': {'k3': 'v3'}}),
    ('s1.k1=v1, s1.k2=v2, s2.k3=v3',
     {'s1': {'k1': 'v1', 'k2': 'v2'}, 's2': {'k3': 'v3'}}),
])
def test_ini_type_resolve(input_value, expected_return, ini_type):
    """Verifies the return value of 'resolve' method in 'IniType' Complex type
    """
    assert ini_type.resolve(input_value) == expected_return


@pytest.fixture(scope="module")
def file_root_dir(tmpdir_factory):
    """Prepares the testing dirs for file tests"""
    root_dir = tmpdir_factory.mktemp('complex_file_dir')

    for file_path in ['file1.yml',
                      'arg/name/file2',
                      'defaults/arg/name/file.yml',
                      'defaults/arg/name/file2',
                      'vars/arg/name/file1.yml',
                      'vars/arg/name/file3.yml',
                      'vars/arg/name/nested/file4.yml']:
        root_dir.join(file_path).ensure()

    return root_dir


@pytest.fixture
def file_type(file_root_dir):
    return cli.FileType("arg-name",
                        (file_root_dir.join('vars').strpath,
                         file_root_dir.join('defaults').strpath),
                        None)


@pytest.fixture
def var_file_type(file_root_dir):
    return cli.VarFileType("arg-name",
                           (file_root_dir.join('vars').strpath,
                            file_root_dir.join('defaults').strpath),
                           None)


@pytest.fixture
def list_file_type(file_root_dir):
    return cli.ListFileType("arg-name",
                            (file_root_dir.join('vars').strpath,
                             file_root_dir.join('defaults').strpath),
                            None)


def test_file_type_resolve(file_root_dir, file_type, monkeypatch):
    """Verifies the file complex type"""
    # change cwd to the temp dir
    monkeypatch.setattr("os.getcwd", lambda: file_root_dir.strpath)

    assert file_type.resolve('file1') == file_root_dir.join(
        'file1.yml').strpath
    assert file_type.resolve('file2') == file_root_dir.join(
        'arg/name/file2').strpath
    with pytest.raises(exceptions.FileNotFoundException):
        file_type.resolve('file.yml')


def test_var_file_type_resolve(file_root_dir, var_file_type, monkeypatch):
    """Verifies the file complex type"""
    # change cwd to the temp dir
    monkeypatch.setattr("os.getcwd", lambda: file_root_dir.strpath)

    assert var_file_type.resolve('file1') == file_root_dir.join(
        'file1.yml').strpath
    assert var_file_type.resolve(
        os.path.abspath('file1')) == file_root_dir.join('file1.yml').strpath
    assert var_file_type.resolve('file2') == file_root_dir.join(
        'arg/name/file2').strpath
    assert var_file_type.resolve('file.yml') == file_root_dir.join(
        'defaults/arg/name/file.yml').strpath
    assert var_file_type.resolve('file3') == file_root_dir.join(
        'vars/arg/name/file3.yml').strpath
    assert var_file_type.resolve('nested/file4.yml') == file_root_dir.join(
        'vars/arg/name/nested/file4.yml').strpath

    with pytest.raises(exceptions.FileNotFoundException):
        var_file_type.resolve('file5')


def test_list_of_var_files(file_root_dir, list_file_type, monkeypatch):
    """Verifies the list of files"""
    monkeypatch.setattr("os.getcwd", lambda: file_root_dir.strpath)

    assert list_file_type.resolve('file1') == [
        file_root_dir.join('file1.yml').strpath]
    assert sorted(list_file_type.resolve('file1,file2')) == sorted([
        file_root_dir.join('file1.yml').strpath,
        file_root_dir.join('arg/name/file2').strpath])
    assert list_file_type.resolve('file3.yml,vars/arg/name/file3') == [
        file_root_dir.join('vars/arg/name/file3.yml').strpath]
