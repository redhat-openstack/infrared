# Taken from: https://gist.github.com/miracle2k/3184458
# Credits: Michael Elsdorfer
#
# usage:
# yaml.safe_dump(data, default_flow_style=False)

"""Make PyYAML output an OrderedDict.

It will do so fine if you use yaml.dump(), but that generates ugly,
non-standard YAML code.

To use yaml.safe_dump(), you need the following.
"""

from collections import OrderedDict
from configure import Configuration, ConfigurationError
import logging
import string
import re
import yaml


_MAPPING_TAG = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
logger = logging.getLogger(__name__)


def to_yaml(header, x):
    """formats x to yaml and adds header on top"""

    return """
%(header)s
======================
%(yml)s
----------------------
    """ % {
        "header": header,
        "yml": yaml.safe_dump(x, default_flow_style=False)
    }


def random_generator(size=32, chars=string.ascii_lowercase + string.digits):
    import random
    return ''.join(random.choice(chars) for x in range(size))


def dict_constructor(loader, node):
    if isinstance(node, yaml.nodes.MappingNode):
        loader.flatten_mapping(node)
    return OrderedDict(loader.construct_pairs(node))


@Configuration.add_constructor('join')
def _join_constructor(loader, node):
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])


@Configuration.add_constructor('random')
def _random_constructor(loader, node):
    """
    usage:
        !random <length>
    returns a random string of <length> characters
    """

    num_chars = loader.construct_scalar(node)
    return random_generator(int(num_chars))


def _limit_chars(string, length):
    length = int(length)
    if length < 0:
        raise AttributeError('length to crop shoud be int, not ' + str(length))

    return string[:length]


@Configuration.add_constructor('limit_chars')
def _limit_chars_constructor(loader, node):
    """
    Usage:
        !limit_chars [<string>, <length>]
    Method returns first param cropped to <length> chars.
    """
    params = loader.construct_sequence(node)
    if len(params) != 2:
        raise AttributeError('limit_chars requires two params: string length')
    return _limit_chars(params[0], params[1])


@Configuration.add_constructor('env')
def _env_constructor(loader, node):
    """
    usage:
        !env <var-name>
        !env [<var-name>, [default]]
        !env [<var-name>, [default], [length]]
    returns value for the environment var-name
    default may be specified by passing a second parameter in a list
    length is maximum length of output (croped to that length)
    """
    import os
    # scalar node or string has no defaults, raise KeyError
    # if absent
    if isinstance(node, yaml.nodes.ScalarNode):
        return os.environ[loader.construct_scalar(node)]

    seq = loader.construct_sequence(node)
    var = seq[0]
    if len(seq) >= 2:
        ret = os.getenv(var, seq[1])  # second item is default val

        # third item is max. length
        if len(seq) == 3:
            ret = _limit_chars(ret, seq[2])
        return ret

    return os.environ[var]


class LookupDirective(yaml.YAMLObject):
    """
    Usage
        foo: !lookup bar.baz

    when the yaml is safe-dumped, the foo.bar is looked up in
    LookupDirective.lookup_table. The table should be set prior
    to lookup and should support __getitem__() which accepts
    the string 'foo.bar' and return value for it
    """
    lookup_table = None
    yaml_tag = u'!lookup'
    yaml_dumper = yaml.SafeDumper

    def __init__(self, key):
        self._key = key

    def lookup(self):
        if not LookupDirective.lookup_table:
            logging.debug("no lookup table ")
            return '{{ %s }}' % self._key

        key = self._key
        if self.yaml_tag in key:
            parser = re.compile('\[\s*!lookup\s[^\s]+\s*\]')
            additional_lookups = parser.findall(key)

            for another_lookup in additional_lookups:
                self._key = another_lookup[1:-1].strip().split()[1]
                result = "{0}".format(self.lookup())

                # this is necessary in cases when the key has "." in it like 7.1
                if '.' in result:
                    result = result.replace('.', '<DOT_ANCHOR>')
                key = key.replace(another_lookup, ".{0}".format(result))

            self._key = key

        if hasattr(LookupDirective.lookup_table, 'delimiter'):
            key = key.replace('.', LookupDirective.lookup_table.delimiter)
            if key.find('<DOT_ANCHOR>') != -1:
                key = key.replace('<DOT_ANCHOR>', '.')

        if key not in LookupDirective.lookup_table:
            logging.warn("key %s not in  lookup table ", self._key)
            return '{{ %s }}' % self._key

        return LookupDirective.lookup_table[key]

    def __repr__(self):
        return "%(class)s(%(lookup)s)" % {
            'class': self.__class__.__name__,
            'lookup': self._key
        }
    __str__ = __repr__

    @classmethod
    def from_yaml(cls, loader, node):
        return LookupDirective(loader.construct_scalar(node))

    @classmethod
    def to_yaml(cls, dumper, node):
        value = node.lookup()
        return dumper.represent_data(value)


class OverwriteDirective(yaml.YAMLObject):
    yaml_tag = u'!overwrite'
    yaml_dumper = yaml.SafeDumper

    def __init__(self, value):
        self.value = value

    @classmethod
    def from_yaml(cls, loader, node):
        if isinstance(node, yaml.nodes.ScalarNode):
            return OverwriteDirective(loader.construct_scalar(node))

        if isinstance(node, yaml.nodes.SequenceNode):
            return OverwriteDirective(loader.construct_sequence(node))

        if isinstance(node, yaml.nodes.MappingNode):
            return OverwriteDirective(loader.construct_mapping(node))

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_data(data.value)


def patch_configure_getattr(self, name):
    if name.startswith('__'):
        raise AttributeError(name)
    return self[name]
Configuration.__getattr__ = patch_configure_getattr


def patch_configure_merge(self, config):
    from copy import deepcopy
    from collections import Mapping, Sequence
    for k, v in config.items():
        if k not in self:
            self[k] = deepcopy(v)
            continue

        if isinstance(v, OverwriteDirective):
            self[k] = deepcopy(v.value)
            continue

        if type(self[k]) != type(v):
            raise ConfigurationError(
                "cannot merge type '%s' with type '%s' for key '%s'" % (
                    self[k].__class__.__name__,
                    v.__class__.__name__,
                    k
                ))

        if isinstance(v, Mapping):
            patch_configure_merge(self[k], v)
        elif isinstance(v, Sequence) :
            if hasattr(self[k], 'extend'):
                self[k].extend(v)
            else:
                self[k] = deepcopy(v)
        elif hasattr(self[k], 'extend'):
            self[k].extend(v)
        else:
            self[k] = deepcopy(v)

    return self

Configuration.merge = patch_configure_merge


def represent_odict(dump, tag, mapping, flow_style=None):
    """Like BaseRepresenter.represent_mapping, but does not issue the sort().
    """
    value = []
    node = yaml.MappingNode(tag, value, flow_style=flow_style)
    if dump.alias_key is not None:
        dump.represented_objects[dump.alias_key] = node
    best_style = True
    if hasattr(mapping, 'items'):
        mapping = mapping.items()
    for item_key, item_value in mapping:
        node_key = dump.represent_data(item_key)
        node_value = dump.represent_data(item_value)
        if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
            best_style = False
        if not (isinstance(node_value, yaml.ScalarNode)
                and not node_value.style):
            best_style = False
        value.append((node_key, node_value))
    if flow_style is None:
        if dump.default_flow_style is not None:
            node.flow_style = dump.default_flow_style
        else:
            node.flow_style = best_style
    return node


def register():
    from ksgen.tree import OrderedTree

    yaml.add_constructor(_MAPPING_TAG, dict_constructor)

    yaml.SafeDumper.add_representer(
        OrderedTree,
        lambda dumper, value: represent_odict(
            dumper, u'tag:yaml.org,2002:map', value)
    )
    yaml.SafeDumper.add_representer(
        Configuration,
        lambda dumper, value: represent_odict(
            dumper, u'tag:yaml.org,2002:map', value)
    )
    yaml.SafeDumper.add_representer(
        OrderedDict,
        lambda dumper, value: represent_odict(
            dumper, u'tag:yaml.org,2002:map', value)
    )
