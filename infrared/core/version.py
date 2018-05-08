"""This module handles pbr version"""

from pbr import version as pbr_version
from ansible import __version__ as ansible_version
import platform

version_info = pbr_version.VersionInfo("infrared")


def version_string():
    return "%s (ansible-%s, python-%s)" % (
        version_info.semantic_version().release_string(),
        ansible_version,
        platform.python_version()
        )
