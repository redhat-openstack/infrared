"""This module provides helper methods for dict merging and dict insertion. """

from infrared.core.utils import logger

LOG = logger.LOG


def dict_insert(dic, val, key, *keys):
    """insert a value of a nested key into a dictionary

    to insert value for a nested key, all ancestor keys should be given as
    method's arguments

    example:
      dict_insert({}, 'val', 'key1.key2'.split('.'))

    :param dic: a dictionary object to insert the nested key value into
    :param val: a value to insert to the given dictionary
    :param key: first key in a chain of key that will store the value
    :param keys: sub keys in the keys chain
    """
    if dic is None:
        return

    if not keys:
        if isinstance(dic.get(key, None), dict) and isinstance(val, dict):
            dict_merge(dic[key], val)
        else:
            dic[key] = val
        return

    dict_insert(dic.setdefault(key, {}), val, *keys)


class ConflictResolver(object):
    """Resolves conflicts while merging dicts. """

    @staticmethod
    def none_resolver(first, second, key):
        """Replaces value in first dict only if it is None.

        Appends second value into the first in type is list.
        """

        # tyr to merge lists first
        if isinstance(first[key], list):
            if isinstance(second[key], list):
                first[key].extend(second[key])
            elif second[key] is not None:
                first[key].append(second[key])

        if key not in first or first[key] is None:
            first[key] = second[key]

    @staticmethod
    def greedy_resolver(first, second, key):
        """Replace always first with the value from second """
        first[key] = second[key]

    @staticmethod
    def unique_append_list_resolver(first, second, key):
        """Merges first and second lists """
        if isinstance(first[key], list) and isinstance(second[key], list):
            for item in second[key]:
                if item not in first[key]:
                    first[key].append(item)
        else:
            return ConflictResolver.greedy_resolver(first, second, key)


def dict_merge(first, second,
               conflict_resolver=ConflictResolver.greedy_resolver):
    """Merge `second` dict into `first`.

    :param first: Modified dict
    :param second: Modifier dict
    :param conflict_resolver: Function that resolves a merge between 2 values
        when one of them isn't a dict
    """
    for key in second:
        if key in first:
            if isinstance(first[key], dict) and isinstance(second[key], dict):
                dict_merge(first[key], second[key],
                           conflict_resolver=conflict_resolver)
            else:
                # replace first value with the value from second
                conflict_resolver(first, second, key)
        else:
            try:
                first[key] = second[key]
            except TypeError as e:
                LOG.error("dict_merge(%s, %s) failed on: %s" % (first, second, key))
                raise e
