def add_prefix(value, prefix=''):
    """Add string prefix to item.

    {{ ['hanukkah', 'easter', 'pessah'] | map('add_prefix', 'happy ' }}
    -> ['happy hanukkah', 'happy easter', 'happy pessah']
    """

    return ''.join((prefix, value))


class FilterModule(object):

    def filters(self):
        return {
            'add_prefix': add_prefix,
        }
