import os
import pytest
from infrared.core.cli import cli


@pytest.fixture
def list_value_type():
    """
    Create a new list value complex type
    """
    return cli.ListValue("test", [os.getcwd(), ], 'cmd')


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
