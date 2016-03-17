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
      "nested2": {"netsted3":
                      {"needle": "val3",
                       "differnt": "values"}},
      "nested1": {"needle": "val2", "differnt": "values"}
      }, ["val1", "val2", "val3"]),
    ({"bad": "input",
      "needle": {"netsted3":
                      {"needle": "val3",
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
    from utils import search_tree

    result = search_tree(haystack, "needle")
    # can't make set of dict, but we still don't care about order
    assert len(result) == len(output)
    for item in output:
        assert item in result
