units = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']


def from_bytes(num, unit=''):
    for u in units:
        if u == unit:
            return num
        num /= 1024.0


def to_bytes(num, unit=''):
    for u in units:
        if u == unit:
            return num
        num *= 1024.0


def filesize(value, target_unit=''):
    """Convert file sizes to float in requested target units.

    {{ 1K | filesize() }}
    -> 1024
    {{ 1G | filesize('M') }}
    -> 1024
    {{ 1K | filesize('M') }}
    -> 0.0009765625
    """

    base_num, base_unit = value, ''
    if value[-1] in units[1:]:
        base_num, base_unit = value[:-1], value[-1]

    return from_bytes(to_bytes(float(base_num), base_unit), target_unit)


class FilterModule(object):

    def filters(self):
        return {
            'filesize': filesize
        }
