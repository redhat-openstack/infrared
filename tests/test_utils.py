import pytest


@pytest.mark.parametrize('tested, val, key, expected', [
    ({}, 'val', ['key'], {'key': 'val'}),

    ({}, 'val', ['key1', 'key2', 'key3'], {'key1': {'key2': {'key3': 'val'}}}),

    ({'a_key': 'a_val', 'b_key1': {'b_key2': {'b_key3': 'b_val'}}}, 'x_val',
     ['b_key1', 'b_key2'], {'a_key': 'a_val', 'b_key1': {'b_key2': 'x_val'}}),
])
def test_dict_insert(tested, val, key, expected):
    from cli import utils
    utils.dict_insert(tested, val, *key)
    assert tested == expected
