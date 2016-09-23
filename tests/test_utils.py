import pytest


@pytest.mark.parametrize('tested, val, key, expected', [
    ({}, 'val', ['key'], {'key': 'val'}),

    ({}, 'val', ['key1', 'key2', 'key3'], {'key1': {'key2': {'key3': 'val'}}}),

    ({'a_key': 'a_val', 'b_key1': {'b_key2': {'b_key3': 'b_val'}}}, 'x_val',
     ['b_key1', 'b_key2'], {'a_key': 'a_val', 'b_key1': {'b_key2': 'x_val'}}),
])
def test_dict_insert(tested, val, key, expected):
    from infrared.core.utils import utils
    utils.dict_insert(tested, val, *key)
    assert tested == expected


def test_dict_merge():
    from infrared.core.utils.utils import dict_merge

    first_dict = {'a': 1, 'b': 2, 'c': {'d': 'foo1', 'e': 'bar', 'list1': [
        'a', 'b', 'c']}, 'list2': [1, 2, 3]}
    second_dict = {'a': 2, 'c': {'d': 'foo2', 'f': 5, 'list1': [3, 4, 5]},
                   'g': 'bla', 5: 'yy', 'list3': ['a', 2]}
    expected_result = {'a': 2, 'b': 2, 'c': {'d': 'foo2', 'e': 'bar', 'f': 5,
                                             'list1': [3, 4, 5]}, 'g': 'bla',
                       5: 'yy', 'list2': [1, 2, 3], 'list3': ['a', 2]}

    dict_merge(first_dict, second_dict)

    assert not cmp(first_dict, expected_result)


@pytest.mark.parametrize("first, second, expected", [
    [dict(a=None, b=1, c=[1, 2, 3]),
     dict(a=2, b=3, c=[4, 5]),
     dict(a=2, b=1, c=[1, 2, 3, 4, 5])],

    [dict(a={'b': 1, 'c': 2}, e=[1, ]),
     dict(a={'f': 3}, e=4, d=5),
     dict(a={'b': 1, 'c': 2, 'f': 3}, e=[1, 4], d=5)]
])
def test_dict_merge_none_resolver(first, second, expected):
    from infrared.core.utils.utils import dict_merge, ConflictResolver

    dict_merge(first, second, conflict_resolver=ConflictResolver.none_resolver)
    assert not cmp(first, expected)


@pytest.mark.parametrize("haystack, output", [
    ({}, []),
    ({"needle": "val1",
      "bad": "input"}, ["val1"]),
    ({"needle": "val1",
      "bad": "input",
      "nested1": {"needle": "val2", "differnt": "values"}
      }, ["val1", "val2"]),
    ({"needle": "val1",
      "bad": "input",
      "nested2": {"netsted3": {"needle": "val3",
                               "differnt": "values"}},
      "nested1": {"needle": "val2", "differnt": "values"}
      }, ["val1", "val2", "val3"]),
    ({"bad": "input",
      "needle": {"netsted3": {"needle": "val3",
                              "differnt": "values"}},
      "nested1": {"needle": "val2", "differnt": "values"}
      }, ["val2", "val3",
          {"netsted3": {"needle": "val3", "differnt": "values"}}]),
    ({"bad": "input",
      "list": [{"needle": {"netsted3": {"needle": "val3",
                                        "differnt": "values"}},
                "nested1": {"needle": "val2", "differnt": "values"}}]
      }, ["val2", "val3",
          {"netsted3": {"needle": "val3", "differnt": "values"}}])

])
def test_search_tree(haystack, output):
    from infrared.core.utils.utils import search_tree

    result = search_tree("needle", haystack)
    # can't make set of dict, but we still don't care about order
    assert len(result) == len(output)
    for item in output:
        assert item in result
