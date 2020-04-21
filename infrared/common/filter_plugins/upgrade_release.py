""" Jinja filter to calculate the next release from a given release """

def _get_upgrade_release(value, jump):
    """ Auxiliary function to calculate the next release
        we want to upgrade to, depending on the jump
        parameter.
    """
    new_release_map = {
            '13': '16.1',
            '15': '16.1',
    }

    incr_release = int(value) + jump
    if incr_release < 16:
        return str(incr_release)
    else:
        if str(value) in new_release_map.keys():
            return new_release_map[str(value)]
        else:
            raise ValueError("release %s not mapped yet, please add into filter"
                             % str(value))

def upgrade_release(value):
    """ Input value: String with RHOS release number
        Output value: Next release to upgrade to in String format.

        Examples:

        {{ '7' | upgrade_release }} -> '8'
        {{ '14' | upgrade_release }} -> '15'
        {{ '15' | upgrade_release }} -> '16.1'

    >>> upgrade_release('7')
    '8'
    >>> upgrade_release(14)
    '15'
    >>> upgrade_release('15')
    '16.1'
    """

    return _get_upgrade_release(value, 1)

def ffwd_release(value):
    """ Input value: String with RHOS release number
        Output value: Release to fast forward to in String format.

        Examples:

        {{ '10' | upgrade_release }} -> '13'
        {{ '13' | upgrade_release }} -> '16.1'

    >>> ffwd_release('10')
    '13'
    >>> ffwd_release('13')
    '16.1'
    """

    return _get_upgrade_release(value, 3)


class FilterModule(object):

    def filters(self):
        return {
            'upgrade_release': self.upgrade_release,
            'ffwd_release': self.ffwd_release,
        }

