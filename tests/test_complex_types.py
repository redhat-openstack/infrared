import os

import pytest

from infrared.core.cli import cli


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
