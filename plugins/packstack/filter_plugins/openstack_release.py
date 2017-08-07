"""Jinja filters to streamline openstack versions for numbers and names"""


def _calc_version_from_release(release):
    GRIZZLY = ord("G".lower())
    GRIZZLY_NUMERIC = 3
    return GRIZZLY_NUMERIC - GRIZZLY + ord(release[0].lower())


def _discover_version(value):
    try:
        return int(value), "OSP"
    except ValueError:
        return _calc_version_from_release(value), "RDO"


def openstack_release(value):
    """Convert release name or number to a numeric value

    {{ 7 | openstack_release }}
    -> 7
    {{ "8" | openstack_release }}
    -> 8
    {{ "Liberty" | openstack_release }}
    -> 8

    >>> openstack_release(7)
    7
    >>> openstack_release("7")
    7
    >>> openstack_release("Liberty")
    8
    """

    return _discover_version(value)[0]


class FilterModule(object):

    def filters(self):
        return {
            'openstack_release': openstack_release,
        }
