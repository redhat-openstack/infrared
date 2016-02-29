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


def test_dict_merge():
    from cli.utils import dict_merge

    first_dict = {'a': 1, 'b': 2, 'c': {'d': 'foo1', 'e': 'bar'}}
    second_dict = {'a': 2, 'c': {'d': 'foo2', 'f': 5}, 'g': 'bla', 5: 'yy'}
    expected_result = {'a': 2, 'b': 2, 'c': {'d': 'foo2', 'e': 'bar',
                                             'f': 5}, 'g': 'bla', 5: 'yy'}

    dict_merge(first_dict, second_dict)

    assert not cmp(first_dict, expected_result)
