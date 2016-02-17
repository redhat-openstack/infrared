"""
Usage:
    python test_tree.py <method_name>
    py.test test_tree.py [options]
"""

import logging

from ksgen.tree import OrderedTree, is_dict
from ksgen import yaml_utils
from test_utils import _enable_logging, main


yaml_utils.register()


def print_yaml(msg, x):
    logging.info(yaml_utils.to_yaml(msg, x))


def test_yaml_dump():
    tree = OrderedTree()
    tree['os'] = ['Sunil', 'Thaha']
    tree['os.test'] = ['Sunil', 'Thaha']
    logging.debug(tree)
    print_yaml("tree:", tree)


def test_in():
    _enable_logging()
    tree = OrderedTree()
    tree['a.b.c.d'] = 'foo'
    assert 'a' in tree
    assert 'a.b' in tree
    assert 'a.b.c' in tree
    assert 'a.b.c.d' in tree
    assert 'a.b.c.d.foo' not in tree
    assert 'x' not in tree
    assert 'x.y.z' not in tree
    print_yaml("tree", tree)


def test_merge_2():
    src = OrderedTree()
    src['foo.bar.baz'] = 'boo boo'

    other = OrderedTree()
    other['x.y.z'] = 'xyz'
    other['foo.bar.soo'] = 'moo moo'
    # other['foo.bar.baz.too'] = 'moo moo'
    src.merge(other)
    print_yaml("add merge src and other", src)

    src.merge(other)
    print_yaml("add merge src and other", src)


def test_merge():
    src = OrderedTree()
    src['a.b.c'] = 'foo'
    src['a.b.d'] = 'foo'
    print_yaml('src:', src)

    other = OrderedTree()
    other['x.y.z'] = 'foobar'
    print_yaml('other_tree:', other)

    src.merge(other)
    print_yaml("After updating x.y.z: ", src)
    assert 'a.b.c' in src
    assert 'a.b.d' in src
    assert 'x.y.z' in src
    assert src['a.b.d'] == 'foo'

    other['a.b.d.e'] = 'foobar'
    print_yaml('add a.b.d.e to other:', other)
    print_yaml('src:', src)

    src.merge(other)

    print_yaml("After merge: ", src)
    assert 'a.b.c' in src
    assert 'a.b.d' in src
    assert 'x.y.z' in src
    assert 'a.b.d.e' in src
    assert src['a.b.d'] != 'foo'


def test_merge_dict_objects():
    tree = OrderedTree()
    tree['foo'] = 'foo'
    tree['bar'] = 'baz'
    obj = {
        "test": "foo",
        "foo":  "bar"
    }

    tree.merge(obj)
    print_yaml("updating a simple dict", tree)
    assert 'test' in tree
    assert 'foo' in tree
    assert isinstance(tree['foo'], OrderedTree) is False
    assert tree['test'] == 'foo'
    assert tree['foo'] == 'bar'
    assert tree['bar'] == 'baz'

    # add to existing tree
    replace_bar = {
        "bar": {
            "baz": {
                "boo": "baaaad"
            }
        }
    }
    tree.merge(replace_bar)
    print_yaml("replace bar with a dict", tree)
    assert 'test' in tree
    assert 'foo' in tree
    assert 'bar' in tree
    assert isinstance(tree['foo'], OrderedTree) is False
    assert isinstance(tree['bar'], OrderedTree)
    assert tree['test'] == 'foo'
    assert tree['foo'] == 'bar'
    assert tree['bar.baz.boo'] == 'baaaad'
    assert isinstance(tree['bar.baz'], OrderedTree)

    # add more values to the existing dictionary
    add_to_bar = {
        "bar": {
            "too": {
                "moo": "yo yo"
            }
        }
    }
    tree.merge(add_to_bar)
    print_yaml("replace bar with a dict", tree)

    assert 'test' in tree
    assert 'foo' in tree
    assert 'bar' in tree
    assert isinstance(tree['foo'], OrderedTree) is False
    assert isinstance(tree['bar'], OrderedTree)
    assert tree['test'] == 'foo'
    assert tree['foo'] == 'bar'
    assert tree['bar.baz.boo'] == 'baaaad'
    assert isinstance(tree['bar.baz'], OrderedTree)
    assert tree['bar.too.moo'] == 'yo yo'
    assert isinstance(tree['bar.too'], OrderedTree)

    # assert 'root.test' in tree
    # assert 'root.foo' in tree
    # assert 'root.bar' in tree
    # assert isinstance(tree['root'], OrderedTree)
    # assert isinstance(tree['root.foo'], OrderedTree) is False
    # assert tree['root.test'] == 'foo'
    # assert tree['root.foo'] == 'bar'
    # print_yaml("inserting a complex dict", tree)

    # replace_foo = {
    #     # 'foo': {
    #          # 'bar': 'baz'
    #     # }
    # }
    # tree.insert('root', replace_foo)
    # assert 'root.test' in tree
    # assert 'root.foo' in tree
    # assert 'root.bar' in tree
    # assert isinstance(tree['root'], OrderedTree)
    # assert isinstance(tree['root.foo'], OrderedTree)
    # assert isinstance(tree['root.foo.bar'], OrderedTree) is False
    # assert tree['root.foo'] != 'bar'


def test_del():
    t = OrderedTree()
    t['foo.bar.baz'] = 'good'
    t['foo.bar.boz'] = 'good'
    t['foo.zoo.yoo'] = 'good'

    print_yaml("initial tree", t)

    assert 'foo' in t
    assert 'foo.bar.baz' in t
    assert 'foo.bar.boz' in t
    assert 'foo.zoo.yoo' in t

    del t['foo.bar.boz']
    print_yaml("del foo.bar.boz", t)

    x = t['foo']

    del x['bar']
    assert 'foo.bar' not in t
    assert 'foo.bar.baz' not in t
    print_yaml("del foo.bar", t)

    del x['zoo']
    assert 'foo' in t
    assert 'foo.zoo' not in t
    print_yaml("del foo.zoo", t)

    del t['foo']
    assert 'foo' not in t
    print_yaml("del foo", t)


def test_insert():
    tree = OrderedTree()
    logging.debug(tree)
    tree.insert('foo.bar', 'moomoo')
    assert 'foo' in tree
    assert 'foo.bar' in tree
    assert tree['foo.bar'] == 'moomoo'
    assert tree['foo']['bar'] == 'moomoo'

    print_yaml("After foo.bar", tree)

    tree.insert('foobar', 'moomoo')
    tree.insert('foo.bar.baz', 'moomoo')

    assert tree['foo.bar'] != 'moomoo'
    assert tree['foo.bar.baz'] == 'moomoo'

    print_yaml("foo.bar overridden ", tree)

    x = tree['foo.bar']
    x['x.y.z'] = 'blah blah'
    print_yaml("sub-tree x", x)
    print_yaml("extend sub-tree foo.bar ", tree)

    assert x['x.y.z'] == 'blah blah'
    assert 'foo' in tree
    assert 'foo.bar' in tree
    assert tree['foo.bar.x.y.z'] == 'blah blah'


def test_insert_complex_objects():
    tree = OrderedTree()
    obj = {
        "test": "foo",
        "foo":  "bar"
    }

    tree.insert('root', obj)
    print_yaml("After inserting a dict", tree)
    assert 'root.test' in tree
    assert 'root.foo' in tree
    assert isinstance(tree['root'], OrderedTree)
    assert isinstance(tree['root.foo'], OrderedTree) is False
    assert tree['root.test'] == 'foo'
    assert tree['root.foo'] == 'bar'

    # add to existing tree
    another_dict = {
        "bar": {
            "baz": {
                "boo": "baaaad"
            }
        }
    }
    tree.insert('root', another_dict)

    assert 'root.test' in tree
    assert 'root.foo' in tree
    assert 'root.bar' in tree
    assert isinstance(tree['root'], OrderedTree)
    assert isinstance(tree['root.foo'], OrderedTree) is False
    assert tree['root.test'] == 'foo'
    assert tree['root.foo'] == 'bar'
    print_yaml("inserting a complex dict", tree)

    replace_foo = {
        'foo': {
            'bar': 'baz'
        }
    }
    tree.insert('root', replace_foo)
    assert 'root.test' in tree
    assert 'root.foo' in tree
    assert 'root.bar' in tree
    assert isinstance(tree['root'], OrderedTree)
    assert isinstance(tree['root.foo'], OrderedTree)
    assert isinstance(tree['root.foo.bar'], OrderedTree) is False
    assert tree['root.foo'] != 'bar'
    print_yaml("replace foo", tree)

    tree['root.array'] = range(4)

    print_yaml("insert and array", tree)
    assert 'root.array' in tree
    assert isinstance(tree['root.array'], OrderedTree) is False

    tree['root.array.array'] = range(4)
    assert 'root.array' in tree
    assert 'root.array.array' in tree
    assert isinstance(tree['root.array'], OrderedTree)


def test_is_dict():
    import configure
    x = configure.Configuration({'foo': 'bar'})
    assert is_dict(x)


def test_init_dict():
    d = {
        'foo': 'bar'
    }
    tree = OrderedTree('.', **d)
    print_yaml("tree init using a dict", tree)
    assert 'foo' in tree
    assert tree['foo'] == 'bar'

    d2 = {
        'foo': {
            'bar': 'baz'
        }
    }
    tree = OrderedTree('.', **d2)
    print_yaml("tree init using a complex dict", tree)
    assert 'foo.bar' in tree
    assert tree['foo.bar'] == 'baz'

    import configure
    x = configure.Configuration({'foo': 'bar'})
    assert is_dict(x)

# def test_custom_delimiters():
    # t = OrderedTree()
    # t['foo.bar.baz'] = 'moo.moo'
    # s['foo.bar.moo'] = range(4)

    # # del s['foo']['bar']

    # del s['foo.bar']
    # s.insert('foo.rhel.7', [1, 2, 3, 4, 5])
    # s.insert('foo.bar.baz.foobar', [1, 2, 3, 4, 5], '.')
    # s.insert('foo/bar/baz/foobar', [1, 2, 3, 4, 5], '/')

    # logging.debug(yaml.safe_dump(dict(s)))


if __name__ == '__main__':
    main(locals())
