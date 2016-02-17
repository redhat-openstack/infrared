"""
tree: datastructure that can hold heirachial OrderedDicts
"""

from collections import OrderedDict, Mapping
import logging


def enum(**enums):
    return type('Enum', (), enums)


class OrderedTree(OrderedDict):
    """
    A simple nested tree using dict
    """
    # Enum Path
    Path = enum(NoCreate=0, AutoCreate=1)

    def __init__(self, delimiter='.', **kwargs):
        """
        Create a Tree
        """
        super(OrderedTree, self).__init__()
        self.delimiter = delimiter
        self.merge(kwargs)

    def insert(self, key, value, delimiter=None):
        """
        inserts @key to the tree and sets value to @value
        """
        parent = self._parent(key, OrderedTree.Path.AutoCreate, delimiter)
        child = self._key_for_index(key, -1, delimiter)
        logging.debug("parent: %s, child: %s", parent, child)
        OrderedTree._add_child(parent, child, value)

    def merge(self, other):
        for (k, v) in other.iteritems():
            logging.debug("%s, %s", k, v)
            # if the key isn't there, then copy the entire tree
            if k in self:
                logging.debug("%s is in self", k)
                if isinstance(self[k], OrderedTree):
                    logging.debug("merge self[%s] with value: %s", k, v)
                    self[k].merge(v)
                    continue    # ### skip to next one ###

                del self[k]     # self[k] is not a tree so replace it
            OrderedTree._add_child(self, k, v)

    def __contains__(self, key):
        delimiter = self.delimiter
        if delimiter not in key:
            return super(OrderedTree, self).__contains__(key)

        keys = key.split(delimiter)

        node = self
        for key in keys:
            if (not isinstance(node, OrderedTree)
                    or key not in node):
                return False
            node = node[key]
        return True

    def __getitem__(self, key):
        if self.delimiter not in key:
            return super(OrderedTree, self).__getitem__(key)

        parent = self._parent(key)
        leaf = self._key_for_index(key, -1)
        return parent[leaf]

    def __setitem__(self, key, value):
        if self.delimiter not in key:
            super(OrderedTree, self).__setitem__(key, value)
        else:
            self.insert(key, value)

    def __delitem__(self, key):
        if self.delimiter not in key:
            return super(OrderedTree, self).__delitem__(key)

        parent = self._parent(key)
        leaf = self._key_for_index(key, -1)
        del parent[leaf]

    # ### private ###
    def _key_for_index(self, key, index, delimiter=None):
        delimiter = delimiter or self.delimiter
        return key.split(delimiter)[index]

    def _parent(self, path, create_flag=Path.NoCreate, delimiter=None):
        delimiter = delimiter or self.delimiter
        if not path or len(path) == 0:
            raise KeyError()

        keys = path.split(delimiter)
        # create the hierarchy until the last parent,
        # and then add the leaf to the last parent
        # with value
        node = self
        for key in keys[:-1]:
            if (create_flag == OrderedTree.Path.AutoCreate and
                    (not node.__contains__(key) or
                     not isinstance(node[key], OrderedTree))):
                node[key] = OrderedTree(self.delimiter)  # debated
            node = node[key]
        return node

    def _add_child(self, child, value):
        if not is_dict(value):
            logging.debug("value: %s is NOT a dict: copying "
                          "to child: %s ", value, child)
            self[child] = value
            return

        logging.debug("value: %s is dict: DEEP copying "
                      "to  child: %s ", value, child)

        if child not in self:
            logging.debug("child: %s not in "
                          "Parent: %s - CREATING", child, self)
            self[child] = OrderedTree(self.delimiter)
        OrderedTree._deep_copy(self[child], **value)

    def _deep_copy(self, **kwargs):
        for k, v in kwargs.iteritems():
            logging.debug("%s: %s", k, v)
            if not is_dict(v):
                self[k] = v
            else:
                self[k] = OrderedTree(self.delimiter)
                OrderedTree._deep_copy(self[k], **v)


def is_dict(obj):
    """
    returns True is obj is like a dict
    """

    if (isinstance(obj, dict)
            or isinstance(obj, Mapping)):
        return True
    try:
        obj.items()
        return True
    except AttributeError:
        return False
