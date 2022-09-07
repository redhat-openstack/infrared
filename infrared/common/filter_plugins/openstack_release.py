"""Jinja filters to streamline openstack versions for numbers and names"""
import re


def _calc_version_from_release(release):
    GRIZZLY = ord("g")
    GRIZZLY_NUMERIC = 3
    if release[0].lower() > 'w':
        return 18
    if release[0].lower() > 't':
        return 17
    # alphabet reseted, consider it 19 for now
    if release[0].lower() < 'g':
        return 19
    return GRIZZLY_NUMERIC - GRIZZLY + ord(release[0].lower())


def _discover_version(value):
    try:
        try:
            return int(value), "OSP"
        except ValueError:
            # osp can in addition have also 15-trunk and such
            # 16.1 return only the major version
            match = re.search('[0-9]+', value)
            if match:
                return int(match.group()), "OSP"
            raise
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


def openstack_distribution(value):
    """Discover distribution from release name/number

    {{ 7 | openstack_distribution }}
    -> OSP
    {{ "8" | openstack_distribution }}
    -> OSP
    {{ "Liberty" | openstack_distribution }}
    -> RDO

    >>> openstack_distribution(7)
    'OSP'
    >>> openstack_distribution("7")
    'OSP'
    >>> openstack_distribution("Liberty")
    'RDO'
    """

    return _discover_version(value)[1]


class FilterModule(object):

    def filters(self):
        return {
            'openstack_distribution': openstack_distribution,
            'openstack_release': openstack_release,
        }
