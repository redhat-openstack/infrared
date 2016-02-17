"""
Usage:
    python test_tree.py <method_name>
    py.test test_tree.py [options]
"""

from copy import deepcopy
import logging
import pytest

from configure import Configuration, ConfigurationError
from test_utils import print_yaml, verify_key_val, TEST_DIR, main

logger = logging.getLogger(__name__)


def test_simple_merge():
    src_dict = {
        "merge": "src merge",
        "src": 'src only',
        'nested_dict': {
            'merge': 'nested src merge',
            'src': 'nested src only'
        }
    }

    other_dict = {
        "merge": "other merge",
        "other": 'other only',
        'nested_dict': {
            'merge': 'nested other merge',
            'other': 'nested other only'
        }
    }

    src = Configuration.from_dict(src_dict)
    print_yaml("Src", src)

    other = Configuration.from_dict(other_dict)
    print_yaml("Other", other)

    merged = deepcopy(src).merge(other)
    print_yaml("merged", merged)

    print_yaml("Src after merge", src)
    print_yaml("Other after merge", other)

    assert verify_key_val(src, src_dict, 'merge')
    assert verify_key_val(src, src_dict, 'src')
    assert verify_key_val(src, src_dict, 'nested_dict.merge')
    assert verify_key_val(src, src_dict, 'nested_dict.src')

    with pytest.raises(KeyError):
        verify_key_val(src, src_dict, 'other')

    assert verify_key_val(merged, other_dict, 'merge')
    assert verify_key_val(merged, src_dict, 'src')
    assert verify_key_val(merged, other_dict, 'other')
    return


def test_dict_order():
    yaml = """
        too: boo
        loo: too
        foo: bar
        moo:
            - soo
    """
    cfg = Configuration.from_string(yaml).configure()
    assert cfg.keys() == ['too', 'loo', 'foo', 'moo']
    for k in cfg.iterkeys():
        logger.debug('%s', k)
    for k, v in cfg.iteritems():
        logger.debug('%s: %s', k, v)

    print_yaml("src", cfg)


def test_array_extend():
    src_dict = {
        "src": [11, 12, 13],
        "merge": [100, 101, 102],
        'nested_dict': {
            'src': [111, 112, 113],
            'merge': [1000, 1001, 1002]
        }
    }

    other_dict = {
        "other": [22, 22, 23],
        "merge": [200, 202, 202],
        'nested_dict': {
            'other': [222, 222, 223],
            'merge': [2000, 2002, 2002]
        }
    }

    src = Configuration.from_dict(src_dict)
    print_yaml("Src", src)

    other = Configuration.from_dict(other_dict)
    print_yaml("Other", other)

    merged = deepcopy(src).merge(other)
    print_yaml("merged", merged)

    print_yaml("Src after merge", src)
    print_yaml("Other after merge", other)

    assert verify_key_val(src, src_dict, 'merge')
    assert verify_key_val(src, src_dict, 'src')
    assert verify_key_val(src, src_dict, 'nested_dict.merge')
    assert verify_key_val(src, src_dict, 'nested_dict.src')

    with pytest.raises(KeyError):
        verify_key_val(src, src_dict, 'other')

    assert verify_key_val(merged, src_dict, 'src')
    assert verify_key_val(merged, other_dict, 'other')
    assert merged['merge'] == src_dict['merge'] + other_dict['merge']
    assert verify_key_val(merged, src_dict, 'nested_dict.src')
    assert verify_key_val(merged, other_dict, 'nested_dict.other')


def test_merge_lookup():
    lookup_yaml = """
    foo: bar
    merge: !lookup foo
    """

    lookup = Configuration.from_string(lookup_yaml)
    print_yaml("Lookup yaml", lookup)

    new_yaml = """
    merge: baz
    """
    new_values = Configuration.from_string(new_yaml)
    print_yaml("merge", new_values)

    error_raised = True
    with pytest.raises(ConfigurationError):
        logger.debug("Going to merge configs that should fail")
        deepcopy(lookup).merge(new_values)
        logger.critical("You should never see this")
        error_raised = False
    assert error_raised
    logger.debug("Raised ConfigurationError")


def test_overwrite_tag():
    src_yaml = """
    foo: bar
    """

    overwrite_fail_yaml = """
    foo: [1, 2, 3]
    """
    src = Configuration.from_string(src_yaml)
    print_yaml("Src", src)

    overwrite_fail = Configuration.from_string(overwrite_fail_yaml)
    print_yaml("Overwrite fail", overwrite_fail)

    error_raised = True
    with pytest.raises(ConfigurationError):
        logger.debug("Going to merge configs that should fail")
        merged = deepcopy(src).merge(overwrite_fail)
        logger.critical("You should never see this")
        error_raised = False
    assert error_raised
    logger.debug("Raised ConfigurationError")
    assert src.foo == 'bar'

    # ### use overwrite to overwrite src.foo
    overwrite_yaml = """
    foo: !overwrite [1, 2, 3]
    """
    overwrite = Configuration.from_string(overwrite_yaml)
    print_yaml("Overwrite", overwrite)

    merged = deepcopy(src).merge(overwrite)
    print_yaml("Merged", merged)


def test_random():
    src_yaml = """
    random: !random 8

    """
    random_so_far = set()

    for x in range(2 ** 12):
        src = Configuration.from_string(src_yaml)
        if src.random in random_so_far:
            print len(random_so_far)
            assert src.random not in random_so_far
        random_so_far.add(src.random)


def test_env():
    src_yaml = """
    user: !env [USER]
    invalid: !env [DOES_NOT_EXIST1, ~]
    same_user: !env [ DOES_NOT_EXIST2, !env [USER, baaaz] ]
    default: !env [ DOES_NOT_EXIST3, !env [FOOO, default] ]
    home_short: !env [ HOMExxx, '/my/home/under/the/bridge/', 7 ]

    """
    src = Configuration.from_string(src_yaml)
    print_yaml("Src", src)

    assert src.user is not None
    assert src.invalid is None
    assert src.same_user == src.user
    assert src.default == 'default'
    assert src.home_short == '/my/hom'


def test_limit_chars():
    src_yaml = """
    substr: !limit_chars [ 'abcdefghijklmnopqrstuvwxyz', 7 ]
    zero: !limit_chars [ 'abcdefghijklmnopqrstuvwxyz', 0 ]

    """
    src = Configuration.from_string(src_yaml)
    print_yaml("Src", src)

    assert src.substr == 'abcdefg'
    assert src.zero == ''


def test_monkey_patch_merge():
    """
        Monkey patch configure so that merge will
        append lists instead of replacing them
    """
    src_dict = {
        "d1": [1, 2, 3],
        "s": "foo",
        "a": [1, 2, 3],
        "nested_dict": {
            "d1": "ok",
            "d": "ok"
        }
    }
    src = Configuration.from_dict(src_dict)
    print_yaml("Src", src)

    other_dict = {
        "d2": [1, 3, 5],
        "s": "bar",
        "a": [3, 2, 8],
        "nested_dict": {
            "d1": "ok",
            "d": "ok"
        }
    }
    src = Configuration.from_dict(src_dict)
    print_yaml("Src", src)

    other = Configuration.from_dict(other_dict)
    print_yaml("Other", src)

    merged = deepcopy(src).merge(other)
    print_yaml("src", merged)
    print_yaml("Merged", src)
    assert merged['d1'] == [1, 2, 3]
    assert merged['d2'] == [1, 3, 5]
    assert merged['a'] == [1, 2, 3, 3, 2, 8]
    assert merged['s'] == 'bar'

    src = Configuration.from_string("""array: [1, 2, 3] """)
    print_yaml("Original config", src)

    other = Configuration.from_string("""array: [2, 3, 8, 9] """)
    merged = deepcopy(src).merge(other)
    print_yaml("Merged", merged)
    assert merged['array'] == [1, 2, 3, 2, 3, 8, 9]

    # ### test overwrite

    overwrite = Configuration.from_string(""" array: !overwrite [0, 0, 0] """)
    print_yaml("Overwrite", overwrite)

    merged = deepcopy(src).merge(overwrite)
    print_yaml('Merge with overwrite', merged)

    assert merged['array'] == [0, 0, 0]

    another_overwrite = Configuration.from_string(
        "array: !overwrite [1, 1, 1] ")
    print_yaml("Another Overwrite", another_overwrite)

    merged = merged.merge(another_overwrite)
    print_yaml('Merge with another overwrite', merged)

    assert merged['array'] == [1, 1, 1]
    # extend overwritten
    print_yaml("Extending src", src)

    merged = merged.merge(src)
    print_yaml('Merge with src', merged)

    assert merged['array'] == [1, 1, 1, 1, 2, 3]

    from ksgen.tree import OrderedTree
    tree = OrderedTree(delimiter='.')
    tree.update(merged)
    print_yaml("Merged", tree)


def test_lookups_in_extends():
    src = Configuration.from_file(TEST_DIR + '/data/extends/extends.yml')
    print_yaml("Extends using !lookup:", src)
    src.configure()
    from ksgen.yaml_utils import LookupDirective
    LookupDirective.lookup_table = src
    print_yaml("Extends using !lookup:", src)


def test_lookup():
    src_yaml = """
    foo: bar
    ref_foo: !lookup foo
    """

    src = Configuration.from_string(src_yaml, configure=False)
    from ksgen.yaml_utils import LookupDirective
    LookupDirective.lookup_table = src
    print_yaml("yaml for src", src)

    # use previous context ...
    ref_src_foo_yaml = """
    ref_src_foo:  !lookup foo
    missing_lookup: !lookup non.existent.key
    """
    ref_src_foo = Configuration.from_string(ref_src_foo_yaml, configure=False)
    merged = deepcopy(src).merge(ref_src_foo)
    LookupDirective.lookup_table = merged
    print_yaml("yaml that refs src", merged)

    import yaml
    final_config = Configuration.from_string(yaml.safe_dump(merged))
    print_yaml("yaml that refs src", final_config)
    assert final_config.ref_foo == src.foo
    assert final_config.ref_src_foo == src.foo
    assert final_config.missing_lookup == '{{ non.existent.key }}'


def test_ref():
    src_yaml = """
    foo: bar
    ref_foo: !ref:foo
    """

    src = Configuration.from_string(src_yaml)
    print_yaml("yaml for src", src)
    assert src.ref_foo == src.foo

    missing_ref_yaml = """
    foo: bar
    ref_foo: !ref:bar
    """

    raised_key_error = True
    with pytest.raises(KeyError):
        Configuration.from_string(missing_ref_yaml)
        raised_key_error = False
    assert raised_key_error
    logger.debug("Raised KeyError")

    # use previous context ...
    ref_src_foo_yaml = """
    ref_src_foo:  !ref:foo
    """
    ref_src_foo = Configuration.from_string(ref_src_foo_yaml, configure=False)
    merged = deepcopy(src).merge(ref_src_foo)
    merged.configure()
    print_yaml("yaml that refs src", merged)


def test_merge_error():
    src_dict = {
        "d1": [1, 2, 3],
        "s": "foo",
        "a": [1, 2, 3],
        "nested_dict": {
            "d1": "ok",
            "d": "ok"
        }
    }

    other_dict = {
        "d2": "foobar",
        "s": "foobar",
        "a": [3, 4, 5],
        "nested_dict": {
            "d2": "ok",
            "d": {            # ### raises ConfigError
                "foo": "bar"
            }
        }
    }
    src = Configuration.from_dict(src_dict)
    print_yaml("src", src)

    other = Configuration.from_dict(other_dict)
    print_yaml("other", other)

    with pytest.raises(ConfigurationError):
        merged = deepcopy(src).merge(other)
        print_yaml("Merged", dict(merged))
    logger.info("Merge raised configuration error")


if __name__ == '__main__':
    main(locals())
