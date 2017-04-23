"""This module handles pbr version"""

from pbr import version as pbr_version

version_info = pbr_version.VersionInfo("infrared")


def version_string():
    return version_info.semantic_version().release_string()
