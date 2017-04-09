"""Jinja filters to streamline openstack versions for numbers and names"""


def _calc_version_from_release(release):
    GRIZZLY = ord("G".lower())
    GRIZZLY_NUMERIC = 3
    return GRIZZLY_NUMERIC - GRIZZLY + ord(release[0].lower())


def _calc_releae_from_version(version):
    GRIZZLY_NUMERIC = 3
    RELEASE_NAMES = [
        "Grizzly",
        "Havana",
        "Icehouse",
        "Juno",
        "Kilo",
        "Liberty",
        "Mitaka",
        "Newton",
        "Ocata",
        "Pike"
    ]

    try:
        if version.capitalize() in RELEASE_NAMES:
            return version
    except AttributeError:
        pass
    return RELEASE_NAMES[int(version) - GRIZZLY_NUMERIC]


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


def openstack_release_name(value):
    """Convert release name or number to a release name

    {{ 7 | openstack_release }}
    -> "Kilo"
    {{ "8" | openstack_release }}
    -> "Liberty"
    {{ "Liberty" | openstack_release }}
    -> "Liberty"

    >>> openstack_release_name(7)
    'Kilo'
    >>> openstack_release_name("7")
    'Kilo'
    >>> openstack_release_name("Liberty")
    'Liberty'
    """

    return _calc_releae_from_version(value)


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
            'openstack_release_name': openstack_release_name,
        }
